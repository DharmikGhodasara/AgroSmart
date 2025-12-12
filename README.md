AgroSmart - Crop Recommendation (Phase 2)

Setup
1) Create and activate a virtual environment
   - Windows (PowerShell):
     python -m venv .venv
     .venv\\Scripts\\Activate.ps1

2) Install dependencies
   pip install -r requirements.txt

3) Train the model
   python core/ml/train_model.py

   - Dataset path: core/ml/data/crop_dataset.csv
   - Outputs: core/ml/crop_model.joblib and core/ml/label_encoder.joblib

4) Run the server
   python manage.py runserver

Use the Crop Suggestion page at /crop-suggestion/ to test predictions.


"# Agro__Smart" 
