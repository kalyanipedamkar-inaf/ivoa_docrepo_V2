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

from . import db, app
from .__init__ import app, UPLOAD_DIR
from .models import Ivoa, Errata, RFC_link, DOI_Bibcode
from .forms import InfoForm, ErrataForm, MoreInfo, RFCForm, DelForm

blueprint = Blueprint('main', __name__)

#########################################
### Helper: extract metadata from Pdf ###
#########################################

def extract_pdf_metadata(pdf_path, original_filename):
    metadata = {}
    try:
        reader = PdfReader(pdf_path)
        info = reader.metadata or {}

        # Title & Author from PDF
        metadata["title"] = info.get("/Title", "Untitled")
        metadata["author"] = info.get("/Author", "Unknown")
        metadata["abstract"] = info.get("/Subject", "")

        # Parse filename convention: DOCTYPE-DOCNAME-version-date.pdf
        # Example: REC-VOSpace-2.1-20230515.pdf
        fname = original_filename.replace(".pdf", "")
        match = re.match(r"([A-Z]+)-([A-Za-z0-9]+)-(\d+)\.(\d+)-(\d{8})", fname)

        if match:
            doctype, docname, major, minor, datestr = match.groups()
            metadata["doctype"] = doctype
            metadata["docname"] = docname
            metadata["version_major"] = int(major)
            metadata["version_minor"] = int(minor)
            metadata["docdate"] = datetime.strptime(datestr, "%Y%m%d").date()
            metadata["fullname"] = f"{doctype}-{docname}-{major}.{minor}-{datestr}"
        else:
            metadata["doctype"] = "Other"
            metadata["docname"] = fname
            metadata["version_major"] = 1
            metadata["version_minor"] = 0
            metadata["docdate"] = datetime.today().date()
            metadata["fullname"] = fname

        # Not in PDF → placeholders
        metadata["editor"] = ""
        metadata["ivoagroup"] = "Unknown"
        metadata["author_email"] = ""
        metadata["comment"] = ""
        metadata["extra_description"] = ""

    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        metadata = {
            "title": "Unknown",
            "author": "Unknown",
            "docname": "Unknown",
            "version_major": 1,
            "version_minor": 0,
            "doctype": "Other",
            "docdate": datetime.today().date(),
            "fullname": "Doc_v1",
        }

    return metadata


# ----------------------------
# 1-step ingestion (Primary)
# ----------------------------
@blueprint.route('/uploadfile', methods=['GET', 'POST'])
def upload_file_auto():
    """
    Primary ingestion route.
    Upload a .zip/.tar → extract metadata from PDF → create DB entry.
    """
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file selected.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        if filename == '':
            flash("Invalid file.")
            return redirect(request.url)

        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            flash("Invalid file type. Only .zip or .tar allowed.")
            return redirect(request.url)

        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
        file.save(upload_path)

        # Extract into Documents/ (temporary folder first)
        extract_path = os.path.join(
            current_app.config['DOCUMENTS_DIR'],
            os.path.splitext(filename)[0]
        )
        os.makedirs(extract_path, exist_ok=True)

        try:
            if file_ext == '.zip':
                with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                    zip_ref.extractall(path=extract_path)
            elif file_ext == '.tar':
                with tarfile.open(upload_path, 'r') as tar_ref:
                    tar_ref.extractall(path=extract_path)
        except Exception as e:
            flash(f"Failed to extract archive: {str(e)}")
            return redirect(request.url)

        # Find PDF inside extracted folder
        pdf_file = None
        for root, _, files in os.walk(extract_path):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_file = os.path.join(root, f)
                    break

        if not pdf_file:
            flash("No PDF found in archive.")
            return redirect(request.url)

        # Extract metadata from PDF
        metadata = extract_pdf_metadata(pdf_file)
        fullname = metadata["fullname"]

        # Rename folder to fullname
        final_extract_path = os.path.join(current_app.config['DOCUMENTS_DIR'], fullname)
        if extract_path != final_extract_path:
            os.rename(extract_path, final_extract_path)

        # Rename files inside folder → prefix with fullname
        for fname in os.listdir(final_extract_path):
            old_path = os.path.join(final_extract_path, fname)
            ext = os.path.splitext(fname)[1]
            new_path = os.path.join(final_extract_path, fullname + ext)
            os.rename(old_path, new_path)

        # Create DB entry
        new_entry = Ivoa(
            fullname=fullname,
            title=metadata.get("title"),
            author=metadata.get("author"),
            package_path=final_extract_path
        )
        db.session.add(new_entry)
        db.session.commit()

        flash("File uploaded, extracted, and metadata saved (auto).")
        return redirect(url_for('thank_you'))

    return render_template('upload_auto.html')


# ----------------------------
# 2-step ingestion (Secondary)
# ----------------------------
@blueprint.route('/fill_form', methods=['GET', 'POST'])
def fill_form():
    """
    User manually enters metadata.
    Redirects to /uploadfile/<fullname> for zip upload.
    """
    if request.method == 'POST':
        fullname = request.form['fullname']
        title = request.form['title']
        author = request.form['author']

        # Save metadata to DB
        new_entry = Ivoa(
            fullname=fullname,
            title=title,
            author=author
        )
        db.session.add(new_entry)
        db.session.commit()

        flash("Metadata saved. Please upload the zip file.")
        return redirect(url_for('upload_file_manual', fullname=fullname))

    return render_template('fill_form.html')


@blueprint.route('/uploadfile/<fullname>', methods=['GET', 'POST'])
def upload_file_manual(fullname):
    """
    Secondary ingestion route.
    User uploads .zip/.tar AFTER filling metadata form.
    Associates package with existing DB record.
    """
    doc = Ivoa.query.filter_by(fullname=fullname).first()
    if not doc:
        flash("Document metadata not found.")
        return redirect(url_for('fill_form'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file selected.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        if filename == '':
            flash("Invalid file.")
            return redirect(request.url)

        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            flash("Invalid file type. Only .zip or .tar allowed.")
            return redirect(request.url)

        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
        file.save(upload_path)

        # Extract into /Documents/<fullname>/
        extract_path = os.path.join(current_app.config['DOCUMENTS_DIR'], fullname)
        os.makedirs(extract_path, exist_ok=True)

        try:
            if file_ext == '.zip':
                with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                    zip_ref.extractall(path=extract_path)
            elif file_ext == '.tar':
                with tarfile.open(upload_path, 'r') as tar_ref:
                    tar_ref.extractall(path=extract_path)
        except Exception as e:
            flash(f"Failed to extract archive: {str(e)}")
            return redirect(request.url)

        # Rename files inside folder
        for fname in os.listdir(extract_path):
            old_path = os.path.join(extract_path, fname)
            ext = os.path.splitext(fname)[1]
            new_path = os.path.join(extract_path, fullname + ext)
            os.rename(old_path, new_path)

        # Update DB with package path
        doc.package_path = extract_path
        db.session.commit()

        flash("File uploaded and linked to metadata (manual).")
        return redirect(url_for('thank_you'))

    return render_template('upload_manual.html', fullname=fullname)


# ----------------------------
# Generic thank you page
# ----------------------------
@blueprint.route('/thankyou')
def thank_you():
    return render_template('thank_you.html')
