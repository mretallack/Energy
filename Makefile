

run:
	python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt
	. venv/bin/activate && python3 energy.py
