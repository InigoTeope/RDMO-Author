from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure PostgreSQL Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/dept_author_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Author(db.Model):
    __tablename__ = 'authors'  # Match the actual table name
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.Text, nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.camp_id'), nullable=False)

class ResearchAuthor(db.Model):
    __tablename__ = 'research_authors'

    research_id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, nullable=False)

    # You can add other attributes if needed

    def serialize(self):
        return {
            'research_id': self.research_id,
            'author_id': self.author_id
        }

class ResearchData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_year = db.Column(db.String(20), nullable=False)
    type_of_research = db.Column(db.String(100), nullable=False)
    title_of_research = db.Column(db.String(255), nullable=False)
    abstract = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    doi = db.Column(db.String(100), nullable=True)
    full_manuscript = db.Column(db.Text, nullable=True)
    journal_publisher = db.Column(db.String(255), nullable=True)
    date_of_publication = db.Column(db.String(50), nullable=True)
    indexing = db.Column(db.String(100), nullable=True)
    apa_format = db.Column(db.Text, nullable=True)
    college_id = db.Column(db.Integer, nullable=False)
    program_id = db.Column(db.Integer, nullable=False)
    authors = db.Column(db.String(255), nullable=False)

class Campus(db.Model):
    __tablename__ = 'campus'  #
    camp_id = db.Column(db.Integer, primary_key=True)
    camp_name = db.Column(db.String(255), nullable=False)

class College(db.Model):
    __tablename__ = 'colleges'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(255), nullable=False)

class Program(db.Model):
    __tablename__ = 'programs'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(255), nullable=False)

# API Routes
@app.route('/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify([{'id': a.id, 'name': a.author_name, 'campus_id': a.campus_id} for a in authors])

@app.route('/researches', methods=['GET'])
def get_research():
    researches = ResearchData.query.all()
    return jsonify([
        {
            'id': r.id,
            'school_year': r.school_year,
            'type_of_research': r.type_of_research,
            'title_of_research': r.title_of_research,
            'abstract': r.abstract,
            'keywords': r.keywords,
            'doi': r.doi,
            'full_manuscript': r.full_manuscript,
            'journal_publisher': r.journal_publisher,
            'date_of_publication': r.date_of_publication,
            'indexing': r.indexing,
            'apa_format': r.apa_format,
            'college_id': r.college_id,
            'program_id': r.program_id,
            'authors': r.authors
        } for r in researches
    ])

@app.route('/author_research/<int:author_id>', methods=['GET'])
def get_author_research(author_id):
    author_researches = db.session.query(ResearchAuthor, ResearchData).join(
        ResearchData, ResearchAuthor.research_id == ResearchData.id
    ).filter(ResearchAuthor.author_id == author_id).all()
    
    data = [{
        'research_id': r.ResearchData.id,
        'title': r.ResearchData.title_of_research,
        'year': r.ResearchData.date_of_publication.year if r.ResearchData.date_of_publication else "Unlabeled",
        'journal_publisher': r.ResearchData.journal_publisher if r.ResearchData.journal_publisher else "Unlabeled",
        'indexing': r.ResearchData.indexing if r.ResearchData.indexing else "Unlabeled",
        'doi': r.ResearchData.doi if r.ResearchData.doi else "Unlabeled",
        'keywords': r.ResearchData.keywords if r.ResearchData.keywords else "Unlabeled"
    } for r in author_researches]
    
    return jsonify(data)




@app.route('/research_authors')
def get_research_authors():
    # Query all rows from the research_authors table
    research_authors = ResearchAuthor.query.all()
    
    # Serialize the data into a list of dictionaries
    result = [research_author.serialize() for research_author in research_authors]
    
    # Return the data as JSON
    return jsonify(result)


@app.route('/campuses', methods=['GET'])
def get_campuses():
    campuses = Campus.query.all()
    return jsonify([
        {'camp_id': c.camp_id, 'camp_name': c.camp_name} for c in campuses
    ])

@app.route('/colleges', methods=['GET'])
def get_colleges():
    colleges = College.query.all()
    return jsonify([
        {'id': c.id, 'college_name': c.college_name} for c in colleges
    ])

@app.route('/programs', methods=['GET'])
def get_programs():
    programs = Program.query.all()
    return jsonify([
        {'id': p.id, 'program_name': p.program_name} for p in programs
    ])
if __name__ == '__main__':
    app.run(debug=True)
