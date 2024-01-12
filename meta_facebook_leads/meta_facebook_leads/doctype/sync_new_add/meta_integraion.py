# Copyright (c) 2023, mansy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from facebook_business.adobjects.campaign import Campaign

from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.lead import Lead
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount



@frappe.whitelist()
def get_credentials():
    return frappe.get_doc("Meta Facebook Settings")
"""
curl -i -X GET \
 "https://graph.facebook.com/v18.0/112169175237482?fields=access_token&transport=cors&access_token=EAAUScJW5dsABOxZChx3wfYQZC4SlE9IW3qWSqPpx6MmrZBHaEpPZAJZA2cVLyt5KZBDCmbZBJ8ARU7A1s5XFwoQwSmCJE3kDwN64VOdVzEtMClFlQJlzNLou0wVL4KtiPYGwsGCoPL4q2YzdxESlYJd7YDg3kKdfsJrMzb8NMUuxCkCTeGWSAPEatjfIROdPwmz"
"""
import requests
import json

class Request:
    def __init__(self, url, version, page_id, f_payload=None, params=None):
        self.url = url
        self.version = 'v' + str(version)
        self.page_id = page_id
        self.f_payload = f_payload
        self.params = params
    @property
    def get_url(self):
        return self.url + "/" + self.version + "/" + self.page_id

class RequestPageAccessToken():
    def __init__(self, request):
        self.request = request

    def get_page_access_token(self):
        response = requests.get(self.request.get_url, params=self.request.params, json=self.request.params) 
        if json.dumps(response.json()).get("error"):
            error_message = ""
            error_message += "url" + " : " + str(self.request.get_url) + "<br>"
            error_message += "params" + " : " + str(self.request.params) + "<br>"
            error_message += "<br>"
            for key in json.dumps(response.json()).get("error").keys():
                error_message += key + " : " + str(json.dumps(response.json()).get("error").get(key)) + "<br>"
            frappe.throw(error_message, title="Error")
        else:
            self.page_access_token = json.dumps(response.json()).get("access_token")
            return self.page_access_token

class RequestLeadGenFroms():
    def __init__(self, request):
        self.request = request

    def get_lead_forms(self):
        response = requests.get(self.request.get_url, params=self.request.params, json=self.request.params) 
        if json.dumps(response.json()).get("error"):
            error_message = ""
            error_message += "url" + " : " + str(self.request.get_url) + "<br>"
            error_message += "params" + " : " + str(self.request.params) + "<br>"
            error_message += "<br>"
            for key in json.dumps(response.json()).get("error").keys():
                error_message += key + " : " + str(json.dumps(response.json()).get("error").get(key)) + "<br>"
            frappe.throw(error_message, title="Error")
        else:
            self.lead_forms = json.dumps(response.json()).get("data")
            return self.lead_forms

class AppendForms():
    def __init__(self, lead_forms, doc):
        self.lead_forms = lead_forms
        self.doc = doc
    def append_forms(self):
        if self.doc.force_fetch:
            self.doc.set("table_hsya", [])
            for lead_form in self.lead_forms:
                self.doc.append("table_hsya", {
                    "form_id": lead_form.get("id"),
                    "form_name": lead_form.get("name"),
                    "created_time": lead_form.get("created_time"),
                    "leads_count": lead_form.get("leads_count"),
                    "page": lead_form.get("page"),
                    "questions": json.dumps({"questions":lead_form.get("questions")}),
                })

class ServerScript():
    def __init__(self, doc):
        self.doc = doc
    
    def create_server_script(self):
        self.server_script = frappe.get_doc({
            "doctype": "Server Script",
            "name": self.doc.name,
            "script_type": "Scheduler Event",
            "event_frequency": "Cron",
            "cron_format": "*/30 * * * *",
            "module": "Meta Facebook Leads",
            "script": self.generate_script()
        })
    def generate_script(self):
        script = ""
        script += "from meta_facebook_leads.meta_facebook_leads.doctype.sync_new_add.sync_new_add import FetchLeads\n"
        script += "fetch_leads = FetchLeads(\"" + self.doc.name + "\")\n"
        script += "fetch_leads.fetch_leads()\n"
        return script

class RequestSendLead():
    def __init__(self, request):
        self.request = request
    def send_lead(self):
        response = requests.post(self.request.get_url, params=self.request.params, json=self.request.f_payload) 
        if json.dumps(response.json()).get("error"):
            error_message = ""
            error_message += "url" + " : " + str(self.request.get_url) + "<br>"
            error_message += "params" + " : " + str(self.request.params) + "<br>"
            error_message += "<br>"
            for key in json.dumps(response.json()).get("error").keys():
                error_message += key + " : " + str(json.dumps(response.json()).get("error").get(key)) + "<br>"
            frappe.throw(error_message, title="Error")
        else:
            return json.dumps(response.json())

class FetchLeads():
    def __init__(self, name):
        self.name = name

    @property
    def get_form_ids(self):
        form_ids = []
        for form in self.doc.table_hsya:
            form_ids.append(form.form_id)
        return form_ids
    @frappe.whitelist()
    def fetch_leads(self):
        self.doc = frappe.get_doc("Sync New Add", self.name)
        self.form_ids = self.get_form_ids
        for form_id in self.form_ids:
            defaults = get_credentials()
            #  init Request
            request = Request(defaults.api_url, defaults.graph_api_version,
            self.doc.page_id, None, params={"fields": "access_token", "transport": "cors",
                    "access_token": defaults.access_token})
            # init RequestPageAccessToken
            request_page_access_token = RequestPageAccessToken(request)
            # get page access token
            request_page_access_token.get_page_access_token()
            # init Request
            request = Request(defaults.api_url, defaults.graph_api_version,
            form_id + "/leads", None, params={"access_token": request_page_access_token.page_access_token,
            "fields": "ad_id,ad_name,adset_id,adset_name,\
                campaign_id,campaign_name,created_time,custom_disclaimer_responses,\
                    field_data,form_id,id,home_listing,is_organic,partner_name,\
                        platform,post,retailer_item_id,vehicle"
                                              })
            # init RequestLeadGenFroms
            request_lead_gen_forms = RequestLeadGenFroms(request)
            # get lead forms
            request_lead_gen_forms.get_lead_forms()
            if request_lead_gen_forms.lead_forms:
                # use self.lead_forms
                # fetch all leads then create them using create_lead
                # filter leads by created_time and id to avoid duplication
                self.paginate_lead_forms(request_lead_gen_forms.lead_forms)

                
            
    def paginate_lead_forms(self, lead_forms):
        if lead_forms.paging.get("next"):
            next_page = lead_forms.paging.get("next")
            response = requests.get(next_page)
            lead_forms = json.dumps(response.json()).get("data")
            self.create_lead(lead_forms)
            return self.paginate_lead_forms(lead_forms)
        else:
            if lead_forms:
                self.create_lead(self.lead_forms)
            return lead_forms
    def create_lead(self, leads):
        impot
        for lead in leads:
            if not frappe.db.exists("Lead", {"custom_lead_json": json.dumps(lead)}):
                new_lead = frappe.get_doc({
                    "doctype": "Lead",
                    "first_name": lead.get("field_data")[0].get("values")[0],
                    "email_id": lead.get("field_data")[1].get("values")[0],
                    "mobile_no": lead.get("field_data")[2].get("values")[0] ,
                    "job_title" : lead.get("field_data")[3].get("values")[0],
                    "company_name": lead.get("field_data")[4].get("values")[0],
                    "custom_lead_json" : json.dumps(lead),
                })
                try:
                    new_lead.insert(ignore_permissions=True)
                    # create lead in facebook
                    self.create_lead_in_facebook(new_lead)
                except Exception as e:
                    frappe.log_error(str(e), "error")
                    frappe.log_error(str(lead), "lead")
                    frappe.log_error(str(new_lead), "new_lead")
    def create_lead_in_facebook(self, lead):
        import datetime
        import json
        from meta_facebook_leads.meta_facebook_leads.doctype.sync_new_add.meta_integraion_objects import UserData, CustomData, Payload
        now = datetime.datetime.now()
        unixtime = int(now.timestamp())
        if lead.custom_lead_json:
            payload = Payload(
                event_name=lead.status,
                event_time=unixtime ,
                action_source="system_generated",
                user_data=UserData(frappe._dict(lead.custom_lead_json.get("id"))).__dict__,
                custom_data=CustomData("crm", "ERPNext CRM").__dict__
            )    
            f_payload = frappe._dict({"data": [payload.__dict__]})
            # send request to facebook
            defaults = get_credentials()
            #  init Request
            request = Request(defaults.api_url, defaults.graph_api_version,
            defaults.pixel_id + "/events", f_payload, params={"access_token": defaults.pixel_access_token})
            # init RequestSendLead
            request_send_lead = RequestSendLead(request)
            # send lead
            response = request_send_lead.send_lead()
            frappe.log_error(str(response), "response")


