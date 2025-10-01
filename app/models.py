import os
from . import db
from datetime import datetime, timezone

class Ivoa(db.Model):
    __tablename__ = 'ivoa'

    id = db.Column(db.Integer, primary_key=True)
    ivoagroup = db.Column(db.Text)
    title = db.Column(db.Text)
    docname = db.Column(db.Text)
    version_major = db.Column(db.Integer)
    version_minor = db.Column(db.Integer)
    doctype = db.Column(db.Text)
    docdate = db.Column(db.Date)
    author = db.Column(db.Text)
    editor = db.Column(db.Text)
    abstract = db.Column(db.Text)
    fullname = db.Column(db.Text, unique=True)
    package_path = db.Column(db.Text)
    author_email = db.Column(db.Text)
    comment = db.Column(db.Text)
    extra_description = db.Column(db.Text)
    available_formats = db.Column(db.Text)

    doi_bibcode = db.relationship('DOI_Bibcode', backref='ivoa', uselist=False)
    rfc_link = db.relationship('RFC_link', backref='ivoa', uselist=False)
    errata = db.relationship('Errata', backref='ivoa', lazy='dynamic')

    def __init__(self, fullname, title=None, author=None, package_path=None,
                 docname=None, version_major=None, version_minor=None, doctype=None,
                 docdate=None, editor=None, abstract=None, author_email=None,
                 comment=None, extra_description=None, available_formats=None,
                 ivoagroup=None):
        self.fullname = fullname
        self.title = title
        self.author = author
        self.package_path = package_path
        self.docname = docname
        self.version_major = version_major
        self.version_minor = version_minor
        self.doctype = doctype
        self.docdate = docdate
        self.editor = editor
        self.abstract = abstract
        self.author_email = author_email
        self.comment = comment
        self.extra_description = extra_description
        self.available_formats = available_formats
        self.ivoagroup = ivoagroup

class DOI_Bibcode(db.Model):

    __tablename__ = 'doi_bibcode'

    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.Text)
    bibcode = db.Column(db.Text)
    ivoa_fullname = db.Column(db.Text, db.ForeignKey('ivoa.fullname'))

    def __init__(self,doi,bibcode,ivoa_fullname):
        self.doi = doi
        self.bibcode = bibcode
        self.ivoa_fullname = ivoa_fullname

class RFC_link(db.Model):

    __tablename__ = 'rfc_link'

    id = db.Column(db.Integer, primary_key=True)
    rfc_link = db.Column(db.Text)
    ivoa_fullname = db.Column(db.Text,db.ForeignKey('ivoa.fullname'))

    def __init__(self,rfc_link,ivoa_fullname):
        self.rfc_link = rfc_link
        self.ivoa_fullname = ivoa_fullname

class Errata(db.Model):

    __tablename__ = 'Errata'

    erratum_id = db.Column(db.Integer,primary_key=True)
    erratum_number = db.Column(db.Integer)
    erratum_title = db.Column(db.Text)
    erratum_author = db.Column(db.Text)
    erratum_date = db.Column(db.Integer)
    erratum_accepted_date = db.Column(db.Integer)
    erratum_link = db.Column(db.Text)
    ivoa_fullname = db.Column(db.Text,db.ForeignKey('ivoa.fullname'))
    erratum_status = db.Column(db.Text)

    def __init__(self,erratum_number,erratum_title,erratum_author,erratum_date,erratum_accepted_date,erratum_link,ivoa_fullname,erratum_status):

        self.erratum_number = erratum_number
        self.erratum_title = erratum_title
        self.erratum_author = erratum_author
        self.erratum_date = erratum_date
        self.erratum_accepted_date = erratum_accepted_date
        self.erratum_link = erratum_link
        self.ivoa_fullname = ivoa_fullname
        self.erratum_status = erratum_status
