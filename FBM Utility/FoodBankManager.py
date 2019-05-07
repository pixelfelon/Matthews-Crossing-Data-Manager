from datetime import datetime
import pandas as pd
import requests
import time
import json
import csv
import sys
import os

import mysql.connector


class FBM(object):
	def __init__(self, url):
		self.url = url
		self.session = requests.Session()
		self._grocery_list = None

		database_info = None

		with open(os.path.dirname(os.path.realpath(__file__))+'/database_info.json') as f:
			database_info = json.load(f)

		self.db = mysql.connector.connect(**database_info)
		self.cur = self.db.cursor()

		self.auth()

	@property
	def grocery_list(self):
		if self._grocery_list is None:
			self.cur.execute("SELECT * FROM grocery_list")
			self._grocery_list = self.cur.fetchall()
			self._grocery_list = tuple(i[0] for i in self._grocery_list)
		return self._grocery_list

	def auth(self):
		with open(os.path.dirname(os.path.realpath(__file__))+'/MCFB_Auth.json') as f:
			auth_info = json.load(f)

		payload = {
			'username': auth_info["user"],
			'password': auth_info["password"],
			'location': '1',
			'action': 'Login'
		}
		self.session.post('https://' + self.url + '/login/', data=payload)

	def GetDonors(self):
		try:
			return self.donor_table
		except AttributeError:
			payload = {
				'fileName': "",
				'col[donors.donors_79fe2d07e8]': '1',
				'col[donors.firstName]': '1',
				'col[donors.middleName]': '1',
				'col[donors.lastName]': '1',
				'col[donors.donors_e0feeaff84]': '1',
				'col[donors.donors_730b308554]': '1',
				'col[donors.donors_b4d4452788]': '1',
				'col[donors.streetAddress]': '1',
				'col[donors.city]': '1',
				'col[donors.zipCode]': '1',
				'col[donors.donors_6213775871]': '1',
				'col[donations.donationTypeSum]': '1',
				'conditions[type]': 'And',
				'conditions[1][field]': 'donors.created_at',
				'conditions[1][action]': 'dlte',
				'conditions[1][value]': time.strftime('%Y-%m-%d'),
				'conditions[1][id]': '1',
				'conditions[1][blockType]': 'item',
				'conditions[1][parent]': "",
				'blockCount': '2'
			}
			r = self.session.post('https://' + self.url +
								  '/reports/donor/donors/csv/',
								  data=payload,
								  stream=True)
			r.raw.decode_content = True
			self.donor_table = csv.reader(str(r.raw.data).split('\n'))
		return self.donor_table

	def GetGuestData(self, start, end):
		payload = {
			"filter_0[column]": "visits.visit_on",
			"filter_0[value1]": start.strftime('%Y-%m-%d'),  # start date
			"filter_0[value2]": end.strftime('%Y-%m-%d'),  # start date
			"filter_1[column]": "visitTrack.status",
			"filter_1[value]": "1",
			"filter_2[column]": "",
			"Condition": "1",
			"exportCols[]": ["visits.id as vid",
							 "visits.visit_on",
							 "visits.location_id",
							 "visits.interview_num as inid",
							 "visits.ident1",
							 "visits.ident2",
							 "visitTrack.trackMethod_id",
							 "visitTrack.trackResult",
							 "visitTrack.status",
							 "CONCAT_WS(' ',volunteers.firstname,volunteers.lastname) as volunteer",
							 "CONCAT_WS(' ',volunteers1.firstname,volunteers1.lastname) as volunteer1",
							 "CONCAT_WS(' ',volunteers2.firstname,volunteers2.lastname) as volunteer2",
							 "CONCAT_WS(' ',volunteers3.firstname,volunteers3.lastname) as volunteer3",
							 "outreaches.id as oid",
							 "outreaches.name",
							 "outreaches.outreach_on",
							 "visits.client_id as gid",
							 "clients.firstname",
							 "clients.middlename",
							 "clients.lastname",
							 "clients.dob",
							 "clients.street_address",
							 "clients.apartment",
							 "clients.city",
							 "clients.state",
							 "clients.zipcode",
							 "clients.homeless",
							 "visits.household_total",
							 "visits.age1",
							 "visits.age2",
							 "visits.age3",
							 "visits.age4",
							 "visits.age5",
							 "visits.age6",
							 "visits.age7",
							 "visits.age8",
							 "clients.blackball",
							 "clients.phone",
							 "clients.gender",
							 "clients.marital_status",
							 "clients.spouse",
							 "clients.race",
							 "clients.othersHousehold",
							 "clients.created_at",
							 "clients.updated_at",
							 "cf_guests.cf_guests_7d34e2419c",
							 "cf_guests.cf_guests_9d2a2f9303",
							 "cf_guests.cf_guests_17d08a8412",
							 "cf_guests.cf_guests_3710cf8208",
							 "cf_guests.cf_guests_d065bb34a7",
							 "cf_guests.cf_guests_4ec8e344cf",
							 "cf_guests.cf_guests_6a2493632a",
							 "cf_guests.cf_guests_fcbb2d417d",
							 "cf_guests.cf_guests_ffd85d93a3",
							 "cf_visits.cf_visits_949ce0bf15",
							 "cf_visits.cf_visits_58e172c123"],
			"action": "Export"
		}
		r = self.session.post('https://' + self.url +
							  '/reports/guests/visits2/export/',
							  data=payload,
							  stream=True)
		r.raw.decode_content = True
		guest_table = list(csv.reader(str(r.raw.data).split('\n')))
		headers = guest_table.pop(0)
		guest_table = pd.DataFrame.from_records(guest_table[:-1], columns=headers)
		return guest_table

	def GetDonations(self):
		try:
			return self.donation_table
		except AttributeError:
			payload = {
				'fileName': '',
				'donation_type': '0',
				'col[donors.id]': '1',
				'col[donors.firstName]': '1',
				'col[donors.middleName]': '1',
				'col[donors.lastName]': '1',
				'col[donors.donors_e0feeaff84]': '1',
				'col[donors.donors_b4d4452788]': '1',
				'col[donors.city]': '1',
				'col[donors.state]': '1',
				'col[donors.zipCode]': '1',
				'col[donors.created_at]': '1',
				'col[donors.donors_6213775871]': '1',
				'col[donations.donationType_id]': '1',
				'col[donations.donations_1b458b4e6a]': '1',
				'col[donations.donation_at]': '1',
				'col[donations.donations_41420c6893]': '1',
				'col[donations.donations_f695e975c6]': '1',
				'conditions[type]': 'And',
				'conditions[1][field]': 'donations.donation_at',
				'conditions[1][action]': 'dlte',
				'conditions[1][value]': time.strftime('%Y-%m-%d'),
				'conditions[1][id]': '1',
				'conditions[1][blockType]': 'item',
				'conditions[1][parent]': '',
				'blockCount': '2'
			}
			r = self.session.post('https://' + self.url +
								  '/reports/donor/donations/csv/',
								  data=payload,
								  stream=True)
			r.raw.decode_content = True
			self.donation_table = csv.reader(str(r.raw.data).split('\n'))
		return self.donation_table

	def FindDonationType(self, df):
		df["DonorCategory"] = ""
		lc_grocery_list = [a.lower() for a in self.grocery_list]
		
		for i, row in df.iterrows():
			data_dict = row.to_dict()
			don_type = data_dict["Source of Donation"]
			
			# Reassignment logic for data entered before the new categories existed
			# Waste, Government/DES, Grocery Store
			if don_type == "Business/Corporation/Organization" or don_type == "":
				if "Food" in data_dict["First Name"] and "Waste" in data_dict["Last Name"]:
					don_type = "Waste"
				elif "TEFAP" == data_dict["First Name"]:
					don_type = "Government/DES"
				elif data_dict["First Name"].lower().split("#")[0].strip() in lc_grocery_list:
					don_type = "Grocery Store"
			# Fix capitalization
			if don_type.lower() == "purchased food":
				don_type = "Purchased Food"
			# Reassign fundraising to Business/Corporation/Organization
			if don_type.lower() == "fundraising events":
				don_type = "Business/Corporation/Organization"
			
			# Legacy logic for when there is no category
			# Purchased food
			if don_type == "":
				if "Food Bank" in data_dict["First Name"] and ("Purchased food" in data_dict["Last Name"] or "Purchased food" in data_dict["Last Name"]):
					don_type = "Purchased Food"
			# TEFAP
			if don_type == "":
				if "TEFAP" in data_dict["First Name"]:
					don_type = "Government/DES"
			# Anonymous (classified as individual)
			if don_type == "":
				if "Anonymous" in data_dict["First Name"]:
					don_type = "Individual Donor"
			# Senior Boxes (this must cone before Church)
			if don_type == "":
				if "Senior Boxes" in data_dict["Name of Food Item"] or "Senior Boxes" in data_dict["Memo"]:
					don_type = "Business/Corporation/Organization"
			# Church
			if don_type == "":
				for type in ["church", "st."]:
					if type in data_dict["First Name"].lower() or type in data_dict[
						"Company / Organization Name"].lower():
						don_type = "Churches/Places of Worship"
			# Individual
			if don_type == "":
				if len(data_dict["Company / Organization Name"]) == 0 and len(data_dict["First Name"]) < 20 and len(
						data_dict["Last Name"]) < 20:
					don_type = "Individual Donor"
			# Other Org/Corp
			if don_type == "":
				don_type = "Business/Corporation/Organization"

			df.at[i, "DonorCategory"] = don_type
		return df

	def GetFoodDonations(self, start, end):
		"""
		Gets food donations (report Food Donations)
		
		:param datetime start: Start date
		:param datetime end: End date
		:return dict: Dist table return
		"""

		payload = {
			'donation_type': '1',
			'col[donors.id]': '1',
			'col[donors.donors_79fe2d07e8]': '1',
			'col[donors.firstName]': '1',
			'col[donors.middleName]': '1',
			'col[donors.lastName]': '1',
			'col[donors.donors_e0feeaff84]': '1',
			'col[donors.donors_c42c9d40e7]': '1',
			'col[donors.donors_b4d4452788]': '1',
			'col[donors.streetAddress]': '1',
			'col[donors.apartment]': '1',
			'col[donors.city]': '1',
			'col[donors.state]': '1',
			'col[donors.zipCode]': '1',
			'col[donors.donorType_id]': '1',
			'col[donations.donationType_id]': '1',
			'col[donations.donations_1b458b4e6a]': '1',
			'col[donations.donation_at]': '1',
			'col[donations.donations_1704817e34]': '1',
			'col[donations.donations_0968598e1b]': '1',
			'col[donations.donations_b09ad16128]': '1',
			'col[donations.donations_6af401c28c]': '1',
			'col[donations.donations_f695e975c6]': '1',
			'col[donations.donations_e0a1fae0a3]': '1',
			'col[donations.donations_6058571536]': '1',
			'conditions[type]': 'And',
			'conditions[1][field]': 'donations.donation_at',
			'conditions[1][action]': 'dgte',
			'conditions[1][value]': start.strftime('%Y-%m-%d'),  # start date
			'conditions[1][id]': '1',
			'conditions[1][blockType]': 'item',
			'conditions[2][field]': 'donations.donation_at',
			'conditions[2][action]': 'dlte',
			'conditions[2][value]': end.strftime('%Y-%m-%d'),  # end date
			'conditions[2][id]': '2',
			'conditions[2][blockType]': 'item',
			'blockCount': '3'
		}
		r = self.session.post('https://' + self.url +
							  '/reports/donor/donations/csv/',
							  data=payload,
							  stream=True)
		r.raw.decode_content = True
		donation_table = list(csv.reader(str(r.raw.data).split('\n')))
		headers = donation_table.pop(0)
		donation_table = pd.DataFrame.from_records(donation_table[:-1], columns=headers)
		donation_table = self.FindDonationType(donation_table)
		return donation_table

	def PostDonation(self, D_id, dollars, pounds, D_type, date):
		donation_type = [
			"",
			"Individual Donor",
			"Churches/Places of Worship",
			"Business/Corporation/Organization",
			"Government/DES",
			"Purchased Food",
			"Grocery Store",
			"Waste"
		]

		payload = {
			'action': 'Save Donation & close',
			'donationType_id': '1',
			'donation_at': date,
			'donations_1b458b4e6a': donation_type[int(D_type)],
			'donations_e0a1fae0a3': dollars,
			'donations_f695e975c6': pounds
		}

		r = self.session.post('https://' + self.url +
							  '/create-new-donation/create/did:' + str(D_id) + '/',
							  data=payload)
		return r.status_code

	def AddDonor(self, donor_json):
		params = json.loads(donor_json)
		payload = {
			'donors_1f13985a81': 'N/A',
			'firstName': params['first'],
			'lastName': params['last'],
			'donors_e0feeaff84': params['email'],
			'donors_730b308554': 'N/A',
			'streetAddress': params['street'],
			'city': params['town'],
			'state': params['state'],
			'zipCode': params['zip'],
			'donorType_id': '1',
			'action': 'Save'
		}
		r = self.session.post('https://' + self.url +
							  '/create-new-donation/donor/create/',
							  data=payload)
		return r.status_code


if __name__ == '__main__':
	# set unlimited table display size
	pd.set_option('display.expand_frame_repr', False)

	if len(sys.argv) < 2:
		print("Usage: 'task' <params>etc...")
		exit(1)
	q = FBM("mcfb.soxbox.co")
	if sys.argv[1] == "donors":
		donor_list = q.GetDonors()
		headers = next(donor_list)
		for row in donor_list:
			print("{")
			for a, b in zip(row, headers):
				print("\"" + b + "\": \"" + a + "\",")
			print("},")
	elif sys.argv[1] == "add_donor":
		# json formatted input wih the following params
		# first, last, email, street, tow, state, zip
		print(q.AddDonor(sys.argv[4]))
	elif sys.argv[1] == "add_donation":
		# type user pass donor_id pounds donation_type date (YYYY-MM-DD)
		print(q.PostDonation(sys.argv[2], 0, sys.argv[3], sys.argv[4], sys.argv[5]))
	elif sys.argv[1] == "fooddonations":
		# start-date, end-date (format mm-dd-yyyy
		start = datetime.strptime(sys.argv[2], "%Y-%m-%d")
		end = datetime.strptime(sys.argv[3], "%Y-%m-%d")
		donor_list = q.GetFoodDonations(start, end)
		filename = "out/GetFoodDonations-{}-{}.csv".format(sys.argv[2], sys.argv[3])
		donor_list.to_csv(filename, sep=',')
		print(filename)
	elif sys.argv[1] == "guestdata":
		# start-date, end-date (format mm-dd-yyyy
		start = datetime.strptime(sys.argv[2], "%Y-%m-%d")
		end = datetime.strptime(sys.argv[3], "%Y-%m-%d")
		donor_list = q.GetGuestData(start, end)
		filename = "out/GetGuestData-{}-{}.csv".format(sys.argv[2], sys.argv[3])
		donor_list.to_csv(filename, sep=',')
		print(filename)
