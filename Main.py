import smtplib,imaplib,email
from email.mime import multipart,text,application

__author__="S.R, YT:Imagine Existance"

def format_message(To="",From="",Subject="",Body="",Date="",Attachments=()):
	"""creates a message to send with parameters all set no none"""
	base=multipart.MIMEMultipart()
	if To!="":
		base["To"]=to
	if From!="":
		base["From"]=fro
	if Subject!="":
		base["Subject"]=subject
	if Date!="":
		base["Date"]=Date
	if Body!="":
		base.attach(text.MIMEText(Body))
	for attach in Attachments:
		part=application.MIMEApplication(attach[1],Name=attach[0])
		part["Content-Disposition"]="attachment; filename=\"%s\""%attach[0]
		base.attach(part)
	return base.as_string()

class email_client:
	def __init__(self,user,password,smtp=("smtp.gmail.com",587),imap="imap.gmail.com"):
		"""a simple email client automaticaly set to recive from inbox and send all from one email address, it is pre set to gmail but can be adjusted for."""
		sender=smtplib.SMTP(*smtp)
		sender.starttls()
		sender.login(user,password)
		self._sender=sender
		reciver=imaplib.IMAP4_SSL(imap)
		reciver.login(user,password)
		self._reciver=reciver
		return None
	
	def _byte_form(self,n):
		return bytes(str(n),encoding='utf-8')
	
	def _payload(self,message):
		if message.is_multipart():
			message_p=self._payload(message.get_payload(0))
		else:
			message_p=message.get_payload(None,True)
		return message_p
	
	def _attachments(self,message):
		files=[]
		for attachment in message.walk():
			if attachment.get_content_maintype()=="multipart" and attachment.get("Content-Disposition")==None:
				continue
			files.append((attachment.get_filename(),attachment.get_payload(decode=True)))
		return files
	
	def send(self,to,message,From=""):
		"""sends a message with the predetermined email client"""
		self._sender.sendmail(From,to,message)
		return None
	
	def recive(self,container,message_id,extract=("From","To","Subject","Body","Attachments")):
		"""extracts a message from container with a predetermined extract set"""
		if container!=False:self._reciver.select(container)
		data={}
		b_int=self._byte_form(message_id)
		raw_data=self._reciver.fetch(b_int,"(RFC822)")[1]
		data_dictionary=email.message_from_bytes(raw_data[0][1])
		for get in extract:
			if get not in ("Body","Attachments"):
				data[get]=(data_dictionary[get])
			if get=="Body":
				try:
					data[get]=(self._payload(data_dictionary).decode("utf-8"))
				except UnicodeDecodeError:
					data[get]=""
			if get=="Attachments":
				data[get]=self._attachments(data_dictionary)
		return data
	
	def modify(self,container,id,data,data_modify="+FLAGS"):
		"""adds a flag to emails such as deleted or seen or unseen"""
		""""\\Deleted" is useful"""
		if container!=False:self._reciver.select(container)
		id=self._byte_form(id)
		self._reciver.store(id,data_modify,data)
		return None
	
	def list_count(self,container,list_out=False):
		"""counts how many tags are in a container"""
		if container!=False:self._reciver.select(container)
		if list_out:
			return list(range(1,1+int((self._reciver)[1][0].decode("utf-8"))))
		return int((self._recivers)[1][0].decode("utf-8"))
		
	def expunge(self,container):
		"""gets rid of deleted"""
		if container!=False:self._reciver.select(container)
		self._reciver.expunge()
		return None
	
	def search_count(self,container,tag,list_out=False):
		"""gets number of emails in a container with a tag"""
		if container!=False:self._reciver.select(container)
		if list_out:
			return [int(b.decode("utf8")) for b in self._reciver.search(None,tag)[1][0].split()]
		return len(self._reciver.search(None,tag)[1][0].split())
	
	def search(self,container,tag,number,extract=("From","To","Subject","Body","Attachments","ID")):
		"""searches for a specific email with certain tags"""
		if container!=False:self._reciver.select(container)
		data={}
		b_int=(self._reciver.search(None,tag)[1][0].split())[number]
		raw_data=self._reciver.fetch(b_int,"(RFC822)")[1]
		data_dictionary=email.message_from_bytes(raw_data[0][1])
		for get in extract:
			if get not in ("Body","Attachments"):
				data[get]=(data_dictionary[get])
			if get=="Body":
				try:
					data[get]=(self._payload(data_dictionary).decode("utf-8"))
				except UnicodeDecodeError:
					data[get]=""
			if get=="Attachments":
				data[get]=self._attachments(data_dictionary)
			if get=="ID":
				data[get]=number
		return data
