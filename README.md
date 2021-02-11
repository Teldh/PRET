# PRET: Prerequisite-Enriched Terminology


## Installation:
Prerequisites:

	 Python 3.4 or newer


*1. Creation of the virtual environment:*	
    
   Create a folder in which you want to have the src
   then, open the terminal and enter the following commands:
   
    - pip install virtualenv 
    - virtualenv venv       
    - venv\Scripts\activate
    
*2. Now that you have a virtual environment you can install all the packages required through:*

	-pip install -r requirements.txt 
	
*3. Database creation:*

	- flask db init
	- flask db migrate
	- flask db upgrade
  
  From the python console:

    >>> import nltk
    >>> nltk.download('punkt')
    >>> nltk.download('stopwords')
    >>> nltk.download('wordnet')
    

To start the website insert (with the virtual environment activated): flask run 

Now you can open your browser on http://127.0.0.1:5000/


