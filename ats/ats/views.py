from django.shortcuts import render
from django.http import HttpResponse
from .form import UploadFileForm
from PyPDF2 import PdfReader
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pymongo import MongoClient
import nltk
from nltk.corpus import stopwords

# Download stop words
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['ats_db']
collection = db['job_applications']

def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Save the file manually
            file_name = default_storage.save(file.name, ContentFile(file.read()))
            file_path = default_storage.path(file_name)
            # Read the PDF file content
            content = read_pdf(file_path)
            # Convert content to lowercase
            lowercase_string = content.lower()
            # Split content into a list of words
            list_of_words = lowercase_string.split()
            # Join list back into a string
            cleaned_string = ' '.join(list_of_words)
            # Remove commas from the string
            cleaned_string = cleaned_string.replace(',', '')
            cleaned_string = cleaned_string.split()
            # Remove stop words
            cleaned_string = [word for word in cleaned_string if word not in stop_words]

            name = request.POST.get('name')
            job_desc = request.POST.get('jd')
            print(name, job_desc)
            job_desc = job_desc.lower()
            count = 0
            total = 0
            frequency = {}
            for word in cleaned_string:
                frequency[word] = cleaned_string.count(word)

            sumof = []
            for key, value in frequency.items():
                if key in job_desc:
                    sumof.append(value)

            total = sum(sumof)
            if total > 10:
                total = 10
            score = {
                'total': total,
                'name': name,
                'job_desc': job_desc
            }

            # Store data in MongoDB
            document = {
                'name': name,
                'job_desc': job_desc,
                'total': total
            }
            collection.insert_one(document)

            # Return response
            return render(request, "score.html", score)
    else:
        form = UploadFileForm()

    return render(request, 'index.html', {'form': form})

def read_pdf(file_path):
    pdf_reader = PdfReader(file_path)
    content = ""
    for page in pdf_reader.pages:
        content += page.extract_text()
    return content
