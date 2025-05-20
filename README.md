# 🏥 Health Insurance Policy Recommender Chatbot  
**CS 6374 and CS 6320 - Computational Logic and Natural Language Processing (Spring 2025)**  
University of Texas at Dallas

## 👥 Team Members
- Suraj Jayakumar  
- Kevin Smith  
- Joshua Martin  

## 🎥 Demo  
[Watch on YouTube](https://www.youtube.com/watch?v=xAkL7oUVgog)

## 💡 Project Overview  
This chatbot assists users in selecting health insurance policies based on their individual needs using natural language processing. It integrates an NLP backend with a Botpress chatbot interface and a simple web front-end for easy interaction.

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed:
- Python 3.8+
- [virtualenv](https://pypi.org/project/virtualenv/)
- [Ngrok](https://ngrok.com/)
- [Botpress](https://botpress.com/)

### Installation Steps
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/health-policy-chatbot.git
   cd health-policy-chatbot```

2. **Set up a Python virtual environment**
   
   - On macOS/Linux:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

   - On Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install dependencies**

   ```pip install -r requirements.txt```

4. **Start the Flask backend**

   ```python app.py```

5. **Deploy using ngrok**

   ```ngrok http 5000```

6. **Configure Botpress**
   - Import the provided Botpress workflow.
   - Navigate to the penultimate node (Execute Code card).
   - Replace the placeholder API URL with your ngrok URL.
   - Save and publish the workflow.

## 📂 Project Structure
```
├── /Chatbot/app.py # Flask backend server
├── pipeline.html # Frontend UI
├── /Chatbot/NLP_Semester_Project - 2025 May 05.bpz # Botpress workflow file
├── /TexasFilteredData # Filtered United States HIOS Data
└── README.md
```

## 🛠️ Tech Stack
- **Python**: Flask, pandas, spaCy  
- **Frontend**: HTML/CSS/JS  
- **Bot Framework**: Botpress  
- **Deployment**: Ngrok  

## 📄 License  
This project is for educational purposes only and is not licensed for commercial use.
