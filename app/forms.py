
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, DateField, SelectField, TextAreaField,
                     SubmitField, BooleanField, PasswordField, validators, HiddenField, MultipleFileField,
                     EmailField, URLField)

class InfoForm(FlaskForm):
    doctype = SelectField(u'Type of the Document',
                          choices=[('WD', 'IVOA Working Draft'),
                                   ('PR', 'IVOA Proposed Recommendation'),
                                    ('REC','IVOA Recommendation'),
                                    ('Note', 'IVOA Note'),
                                    ('PEN', 'IVOA Proposed Endorsed Note'),
                                    ('EN', 'IVOA Endorsed Note'),
                                    ('Other', 'Other')])

    title = StringField ('Title', validators=[DataRequired()])
    docname = StringField ('Docname', validators=[DataRequired()])
    version_major = SelectField(
                                choices =[('0','0'),('1','1'),('2','2'),
                                        ('3','3'),('4','4'),('5','5'),
                                        ('6','6'),('7','7'), ('8','8'),('9','9')])

    version_minor = SelectField(
                                choices =[('0','0'),('1','1'),('2','2'),
                                        ('3','3'),('4','4'),('5','5'),
                                        ('6','6'),('7','7'), ('8','8'),('9','9')])
    docdate = DateField('Document Date',format="%Y-%m-%d")

    author = StringField('Author(s)')
    editor = StringField('Editor(s)')
    ivoagroup = SelectField('Responsible I/W Group:',
                            choices=[('Applications', 'Applications'),('Data Access Layer', 'Data Access Layer'),
                                    ('Data Modelling', 'Data Modelling'), ('Grid & Web Services', 'Grid & Web Services'),
                                    ('Resource Registry', 'Resource Registry'), ('Data Curation & Prevention IG', 'Data Curation & Prevention IG'),
                                    ('Standard & Document Process', 'Standard & Document Process'), ('Semantics', 'Semantics'),
                                    ('Document Standards','Document Standards'),('Theory', 'Theory'), ('VO Event', 'VO Event'),
                                    ('VO table', 'VO Table'), ('VO Query Language', 'VO Query Language')])
    abstract = TextAreaField('Abstract')
    extra_description = URLField('Any Extra Description', [validators.Optional()])
    author_email = EmailField('Contact Email')
    file = MultipleFileField('Upload File')
    available_formats = StringField('available_formats', [validators.Optional()])
    comment = TextAreaField('Comments', [validators.Optional()])
    submit = SubmitField('Submit')



class ErrataForm(FlaskForm):
    ivoa_fullname = StringField('Name of the Document')
    erratum_number = IntegerField('Erratum Number')
    erratum_title = StringField('Title of the Erratum')
    erratum_author = StringField('Author')
    erratum_date = DateField('Date last changed')
    erratum_accepted_date = DateField('Date of erratum accepted')
    erratum_link = URLField('Erratum Link')
    submit = SubmitField("Submit")

class MoreInfo(FlaskForm):

    ivoa_fullname = StringField('Name of the Document(Recommendation)')
    doi = StringField('DOI')
    bibcode = StringField('Bibcode')
    submit = SubmitField("Submit")

class RFCForm(FlaskForm):

    ivoa_fullname = StringField('Name of the Document(Proposed Recommendation)')
    rfc_link = URLField('Please enter the RFC link if applicable')
    submit = SubmitField("Submit")

class DelForm(FlaskForm):

    fullname = StringField("Name of the document to be deleted: ")
    submit = SubmitField("Delete")
