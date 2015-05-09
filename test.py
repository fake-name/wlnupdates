#!flask/bin/python
def go():
	from app import models
	models.install_tsvector_indices()


if __name__ == "__main__":
	go()
