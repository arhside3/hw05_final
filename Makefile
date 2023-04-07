WORKDIR = yatube
TEMPLATES-DIR = $(WORKDIR)/templates
MANAGE = python $(WORKDIR)/manage.py

style:
	black -S -l 79 $(WORKDIR)
	isort $(WORKDIR)
	djlint $(TEMPLATES-DIR) --reformat
	flake8 $(WORKDIR)
