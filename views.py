import os
import zipfile, tarfile
import re
from flask import (current_app, render_template, request, redirect, url_for, flash, send_from_directory, abort)
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict
from werkzeug.security import safe_join
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from sqlalchemy import desc
import pathlib

from . import db
from .__init__ import app, UPLOAD_DIR
from .models import Ivoa, Errata, RFC_link, DOI_Bibcode
from .forms import InfoForm, ErrataForm, MoreInfo, RFCForm, DelForm

@app.route('/')
@app.route("/documents/")
def index():

    rec_query = Ivoa.query.filter_by(doctype='REC').order_by(desc(Ivoa.docdate))
    #the 'rec_query' gives the documents from the db which are only Recommendations and are arranged in the descending order by date, to get the most recent version

    most_stable = [{"title": doc.title, "docname": doc.docname, "fullname": doc.fullname, "ivoagroup": doc.ivoagroup, "version_major": doc.version_major, "version_minor": doc.version_minor}

    for doc in rec_query
    ]
    
    
    seen = set()
    unique_doc = []

    for doc in most_stable:
        if doc["title"] not in seen:
            unique_doc.append(doc)
            seen.add(doc['title'])

    return render_template('home.html', most_stable=unique_doc)



#def index():
#    ivoa_db = Ivoa.query.all()
#    return render_template('home.html', ivoa_db=ivoa_db, most_stable=most_stable)

    
@app.route('/new_doc', methods=['GET','POST'])
def fill_form():

    form = InfoForm()

    if form.validate_on_submit():

        title = form.title.data
        docname = form.docname.data
        version_major = form.version_major.data
        version_minor = form.version_minor.data
        docdate = form.docdate.data
        doctype = form.doctype.data
        author = form.author.data
        editor = form.editor.data
        ivoagroup = form.ivoagroup.data
        abstract = form.abstract.data
        author_email = form.author_email.data
        comment = form.comment.data
        extra_description = form.extra_description.data
        fullname = doctype+"-"+docname.replace(" ", "")+"-"+str(version_major)+"."+str(version_minor)+"-"+(str(docdate).replace("-", ""))
        package_path = os.getcwd()+'/documents'+'/'+docname.replace(" ", "")+'/'+(str(docdate).replace("-", ""))
        available_formats = form.available_formats.data

        new_entry = Ivoa(ivoagroup,title,docname,version_major,version_minor,doctype,docdate,author,editor,abstract,fullname,package_path,author_email,comment,extra_description,available_formats)
        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('upload_file'))

    return render_template('fill_form.html',form=form)


@app.route('/thank_you')
def thank_you():
    return render_template('thankyou.html')

@app.route('/add_errata/<fullname>', methods=['GET', 'POST'])
def add_errata(fullname):

    doc_info_1 = Ivoa.query.filter_by(fullname=fullname).first()

    if request.method == 'GET':
        form = ErrataForm(formdata=MultiDict({'ivoa_fullname': doc_info_1.fullname}))
    else:
        form = ErrataForm()

    if form.validate_on_submit():
        ivoa_fullname = form.ivoa_fullname.data
        erratum_number = form.erratum_number.data
        erratum_title = form.erratum_title.data
        erratum_author = form.erratum_author.data
        erratum_date = form.erratum_date.data
        erratum_accepted_date = form.erratum_accepted_date.data
        erratum_link = form.erratum_link.data
        erratum_status = str("") 

        new_erratum = Errata(erratum_number,erratum_title,erratum_author,erratum_date,erratum_accepted_date,erratum_link,ivoa_fullname,erratum_status)
        db.session.add(new_erratum)
        db.session.commit()

        return redirect(url_for('view_db'))
    return render_template('add_errata.html', form=form, doc_info_1=doc_info_1)

@app.route('/add_more/<fullname>', methods=['GET','POST'])
def add_more(fullname):

    doc_info_1 = Ivoa.query.filter_by(fullname=fullname).first()
    doc_info_3 = DOI_Bibcode.query.filter_by(ivoa_fullname=fullname).first()

    if request.method == 'GET':
        form = MoreInfo(formdata=MultiDict({'ivoa_fullname': doc_info_1.fullname}))
    else:
        form = MoreInfo()

    if form.validate_on_submit():

        ivoa_fullname = form.ivoa_fullname.data
        doi = form.doi.data
        bibcode = form.bibcode.data

        moreinfo = DOI_Bibcode(doi,bibcode,ivoa_fullname)
        db.session.add(moreinfo)
        db.session.commit()

        return redirect(url_for('view_db'))
    return render_template('add_more.html', form=form,  doc_info_1=doc_info_1, doc_info_3=doc_info_3)

@app.route('/add_rfc', methods=['GET','POST'])
def rfc():

    form = RFCForm()

    if form.validate_on_submit():
        ivoa_fullname = form.ivoa_fullname.data
        rfc_link = form.rfc_link.data

        rfc = RFC_link(rfc_link,ivoa_fullname)
        db.session.add(rfc)
        db.session.commit()

        return redirect(url_for('view_db'))
    return render_template('add_rfc.html', form=form)


@app.route('/view_db')
def view_db():
    #ivoa_db = Ivoa.query.filter_by(status='REC').all()
    #To view fill list
    ivoa_db = Ivoa.query.all()
    doi_bibcode_db = DOI_Bibcode.query.all()
    rfc_link_db = RFC_link.query.all()
    errata_db = Errata.query.all()
    return render_template('view_db.html', ivoa_db=ivoa_db)

@app.route("/documents/<fullname>")
def doc_landing(fullname):

    doc_info_1 = Ivoa.query.filter_by(fullname=fullname).first()
    doc_info_2 = Errata.query.filter_by(ivoa_fullname=fullname).first()
    doc_info_3 = DOI_Bibcode.query.filter_by(ivoa_fullname=fullname).first()
    doc_info_4 = RFC_link.query.filter_by(ivoa_fullname=fullname).first()
    return render_template('doc_landing.html', doc_info_1=doc_info_1,doc_info_2=doc_info_2,doc_info_3=doc_info_3,doc_info_4=doc_info_4)


@app.route('/documents/<path:fullname>', methods=['GET', 'POST'])
def download(fullname):
    documents = '/var/www/html/docrepo/documents'

    return send_from_directory(directory=documents, filename=fullname, as_attachment=True)

# Upload the Document

@app.route('/uploadfile', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        if filename != '':
	#file_ext gives the the extensions of the uploaded file
            file_ext = os.path.splitext(filename)[1]
	# fname is a temparory variable to get the original filename of the the uploaded file using Pathlib's 'stem' function
            fname = pathlib.Path(filename)
            original_filename = fname.stem
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                flash('Please upload a .zip or .tar file')
                return redirect(url_for('upload_file'))
                #abort(400)
            else:
	#file.save saves the uploaded file in the 'UPLOAD_DIR' with the original name of the uploaded file
                file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
                source=UPLOAD_DIR+"/"+filename
                destination=UPLOAD_DIR+"/"+Ivoa.fullname+file_ext
                os.rename(source,destination)
	#In the step above the saved '.zip' or '.tar' file is renamed

	# Below the '.zip' or '.tar' files are separated and extracted into the 'documents' directory and the folder is renamed as per IVOA standards
	# After renaming the folder, its contents (files inside) are renamed keeping their extensions constant.
                if file_ext == '.zip':
                    with zipfile.ZipFile(destination, 'r') as zip_ref:
                        zip_ref.extractall(path='/var/www/html/docrepo/documents')
                        src= '/var/www/html/docrepo/documents/'+original_filename
                        dst= '/var/www/html/docrepo/documents/'+Ivoa.fullname
                        os.rename(src,dst)
                        for name in os.listdir(dst):
                            extension = os.path.splitext(name)[1]
                            new_dst = dst + '/' + Ivoa.fullname + extension
                            new_src = dst + '/' + name
                            os.rename(new_src, new_dst)
                elif file_ext == '.tar':
                    with tarfile.open(destination, 'r') as tar_ref:
                        tar_ref.extractall(path='/var/www/html/docrepo/documents')
                        src= '/var/www/html/docrepo/documents/'+original_filename
                        dst= '/var/www/html/docrepo/documents/'+Ivoa.fullname
                        os.rename(src,dst)
                        for name in os.listdir(dst):
                            extension = os.path.splitext(name)[1]
                            new_dst = dst + '/' + Ivoa.fullname + extension
                            new_src = dst + '/' + name
                            os.rename(new_src, new_dst)
                else:
                    return redirect(url_for('upload_file'))
                return redirect(url_for('thank_you'))
    return render_template('upload.html')

@app.route('/delete', methods=['GET', 'POST'])
def delete():

    form = DelForm()

    if form.validate_on_submit():

        fullname = form.fullname.data

        record_ivoa = Ivoa.query.get(fullname)
	#record_ivoa = DOI_Bibcode.query.get(fullname)
	#record_ivoa = RFC_link.query.get(fullname)
	#record_ivoa = Errata.query.get(fullname)
	
        db.session.delete(record_ivoa)
        db.session.commit()

        return redirect(url_for('view_db'))
    return render_template('delete.html', form=form)

@app.route('/rec')
def rec():
    
    ivoa_db = Ivoa.query.filter_by(status='REC').all()

    return render_template('rec.html', ivoa_db=ivoa_db)

@app.route('/endorsed_notes')
def endorsed_notes():

    ivoa_db = Ivoa.query.filter_by(status='EN').all()

    return render_template('endorsed_notes.html', ivoa_db=ivoa_db)

@app.route('/note')
def note():

    ivoa_db = Ivoa.query.filter_by(status='Note').all()

    return render_template('note.html', ivoa_db=ivoa_db)

