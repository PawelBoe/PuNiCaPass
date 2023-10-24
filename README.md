# PuNiCaPass
Pass creator for the PuNiCa Student Clubs in Potsdam. Includes QR-Code validation.


## Installation for Development

### Install python virtual environment with dependencies 
- `python3 -m venv ./YOUR_VENV_LOCATION`
- `pip install -r requirements.txt`

### Create a local mock certificate
- `./generate_local_certficiate.sh`

### Initialize the app and db
- `python app.py --initialize --admin_token YOUR_PASSWORD`

### Run the app
- `python app.py --admin_token YOUR_PASSWORD`
- App will be reachable on `https://localhost:5000`
