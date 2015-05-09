#!flask/bin/python
def go():
	from app import models
	models.install_trigram_indices()


if __name__ == "__main__":
	go()
