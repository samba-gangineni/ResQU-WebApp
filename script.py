import requests
from pymongo import MongoClient


# Mongo Connection 
client = MongoClient()
db = client['ResQU']


def post_precausion_fema():
	fema_precausion_url = 'https://www.ready.gov/feeds/fema-mobile-app-hazard-json-feed'
	response = requests.get(fema_precausion_url)
	for precausion in response.json().get("nodes"):
		db['Precausions'].insert_one(precausion.get("node"))
	return True

def get_precausions(lang="English"):
	title, body, hazard_type = [],[],[]
	results = db['Precausions'].find({"language":lang})
	for result in results:
		print(result['title'])
		break

def post_disaster_summary():
	disaster_summary_fema = 'https://www.fema.gov/api/open/v1/DisasterDeclarationsSummaries'
	response = requests.get(fema_precausion_url)
	for precausion in response.json().get("nodes"):
		db['Precausions'].insert_one(precausion.get("node"))
	return True

if __name__ == '__main__':
	get_precausions()

	