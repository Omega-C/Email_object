import smtplib, imaplib, email, time, datetime, asyncio
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

__author__="""Youtube: Imagine Existance, Github: Omega-C, Overall a tired guy"""

def warn(error):
	en=repr(error).split("(")[0]
	print(f"{en}: {str(error)}")

class Error(BaseException):
	"""a base for specialised exceptions"""
	pass

class LoginError(Error):
	"""a base for login errors"""
	pass

class NotFoundError(Error):
	"""a base for specialised index errors"""

class IMAPLoginError(LoginError):
	"""an error raised when IMAP credientials could not be verified"""
	pass

class SMTPLoginError(LoginError):
	"""an error raised when SMTP credentials could not be verified"""
	pass

class FolderNotFoundError(NotFoundError):
	"""an error raised when a folder is not found"""
	pass

class EmailIndexNotFound(NotFoundError):
	"""an error raised when an email index is not found"""
	pass

class File:
	def __init__(self,Name=None,Data=b""):
		"""
		a class to hold file data in an easier to access form
		"""
		self.data=Data
		self.name=Name

	def from_file(self,file_name,Name=None):
		"""saves filedata as an attachable file,
		Name can be set for a custom name instead of the provided file_name
		"""
		with open(file_name,"rb") as file:
			self.data=file.read()
		if Name==None:
			self.name=file_name
		else:
			self.name=Name

	def from_mime(self,ma):
		"""uses ma (MIMEApplication) data to create a File object"""
		self.name=ma.get_filename()
		self.data=ma.get_payload(decode=True)
		return(self)

	def __getattr__(self,attr):
		"""gets attribute payload as value instead of payload having to be called from class"""
		if attr=="payload":
			try:
				new_part=MIMEApplication(self.data,Name=self.name)
			except TypeError:
				new_part=MIMEApplication(b"",Name=self.name)
			new_part["Content-Disposition"]=f"attachment; filename=\"{self.name}\""
			return(new_part)
		raise(AttributeError)

	def __repr__(self):
		"""provides a simplistic summary of the contents"""
		return(f"<File {{Name: \"{self.name}\", Length: {len(self.data)}}}>")

	def __str__(self):
		"""provides a simplistic summary of the contents"""
		return(self.__repr__())

class Body:
	def __init__(self,text="",subtype="plain",charset=None):
		"""
		a class to hold body (text) data for an email.
		"""
		self.text=text
		self.subtype=subtype
		self.charset=charset

	def from_file(self,filename):
		"""saves filedata as an attachable Text field"""
		with open(filename,"r") as file:
			self.text=file.read()

	def from_mime(self,mt):
		"""uses ma (MIMEText) data to create a Body object"""
		self.text=mt.get_payload()
		self.subtype=mt.get_content_subtype()
		self.charset=mt.get_charset()
		return(self)

	def __getattr__(self,attr):
		"""gets attribute payload as value instead of payload having to be called from class"""
		if attr=="payload":
			return(MIMEText(self.text,_subtype=self.subtype,_charset=self.charset))
		raise(AttributeError)

	def __repr__(self):
		"""provides a simplistic summary of the contents"""
		test_text=self.text[:20].replace("\n"," ").replace("\r"," ").replace("\t"," ")+"..."
		return(f"<Body {{Length: {len(self.text)}, Preview: \"{test_text}\"}}>")

	def __str__(self):
		"""provides a simplistic summary of the contents"""
		return(self.__repr__())

class Email:
	def __init__(self,*attachments,**headers):
		"""
		A MIME object expansion
		Headers are taken as input keywords
		"""
		self.base=MIMEMultipart()
		self.headers=headers

		for key in self.headers:
			self.base[key]=self.headers[key]

		all_attachments=[]
		for attachment in attachments:
			if attachment==None:
				continue
			if type(attachment)==list:
				all_attachments+=attachment
			else:
				all_attachments.append(attachment)

		for attachment in all_attachments:
			self.base.attach(attachment.payload)

	def attach(self,attachment):
		"""attaches an attachment, must be an Email friendly class"""
		self.base.attach(attachment.payload)

	def get_attachments(self,**kwargs):
		"""gets attached payloads and returns them in Email friendly formats"""
		pay=self.base.get_payload(**kwargs)
		if type(pay)!=list:
			pay=[pay]
		pay=list(map(self.convert,pay))
		return(pay)

	def set_headers(self,**headers):
		"""sets provided header values"""
		for key in self.headers:
			if self.headers[key]!=None:
				self.base[key]=self.headers[key]

	def convert(self,mimer):
		"""converts a MIME form to an Email friendly form"""
		if type(mimer)==MIMEText:
			return(Body().from_mime(mimer))
		if type(mimer)==MIMEApplication:
			return(File().from_mime(mimer))
		return(mimer)

	def remove_headers(self,**headers):
		"""it removes the provided headers"""
		for key in self.headers:
			if key in self.base:
				del(self.base[key])

	def __repr__(self):
		"""provides a simplistic summary of the contents"""
		return(f"<Email Object {{Attachments: {str(self.get_attachments())}}}>")

	def __str__(self):
		"""provides a simplistic summary of the contents"""
		return(self.__repr__())

	def string(self):
		"""returns a string of data that can be set"""
		return(self.base.as_string())

	def __getattr__(self,attr):
		"""with attr as a header key, the header value will be gotten"""
		if attr in self.base:
			return(self.base[attr])
		else:
			raise(AttributeError)

	def __getitem__(self,item):
		"""acts as __getattr__ but integer values will return Email friendly attachments"""
		if type(item)==int:
			return(self.get_attachments()[item])
		return(self.base[item])

class Static_Client:
	def __init__(self,imap_details,container,details="<>",**kwargs):
		"""
		acts as a more static imaplib client for asyncronous processing, creates a seperate connection that can be closed
		"""
		self.imap_client=imaplib.IMAP4_SSL(imap_details[1])
		try:
			self.imap_client.login(*imap_details[0])
		except Exception:
			warn(IMAPLoginError("!!!Warning!!! IMAP Authentication Not Accepted. Possible Causes:\n\t-Wrong Login Credentials.\n\t-Third Party Access Not Enabled.\n\t-Server Details Are Wrong.\nYou will not be able to use imaplib features such as accessing mail."))
		self.container=container
		self.count=int(self.imap_client.select(self.container,**kwargs)[1][0].decode("utf-8"))
		self.kw=kwargs
		self.branch=details

	def select(self,container,**kwargs):
		"""selects a container"""
		self.container=container
		try:
			self.imap_client.select(container,**kwargs)
		except ValueError:
			raise(FolderNotFoundError(f"Folder \"{container}\" Not Found.")) from None

	def refresh(self):
		"""refreshes data (should be done within handeling)"""
		try:
			self.count=int(self.imap_client.select(self.container,**self.kw)[1][0].decode("utf-8"))
		except ValueError:
			raise(FolderNotFoundError(f"Folder \"{cont}\" Not Found.")) from None

	def noop(self):
		"""does a noop (no-operation)"""
		self.imap_client.noop()

	def close(self):
		"""closes connections"""
		self.imap_client.close()
		self.imap_client.logout()

	def __getattr__(self,attr):
		"""gets an attribute from the client itself, take noop for example, I like that word"""
		return(getattr(self.imap_client,attr))

	def __repr__(self):
		"""provides a simplistic summary of the contents"""
		return(f"<Static Client {{Container: {self.container}, Parent: {self.branch}}}>")

	def __str__(self):
		"""provides a simplistic summary of the contents"""
		return(self.__repr__())

class Email_Client:
	def __init__(self,*login,smtp_server="smtp.gmail.com:587",imap_server="imap.gmail.com",imap_login=None,smtp_login=None):
		"""
		A combined SMTP and IMAP server class
	
		use integer type to act as list, use string to act as traditional

		for further information/uses, look into imaplib, smtplib, and email.mime modules

		search criteria: https://tools.ietf.org/html/rfc3501#section-6.4.4
		"""
		self._bytes=lambda v:{True:lambda:str(v+1),False:lambda:v}[type(v)==int]()
		self._list_return=lambda v:{True:v,False:[v]}[type(v)==list]

		self.email_adress=login[0]
		self.details=f"<Email Client {{Username:{login[0]}, SMTP_Server: {smtp_server}, IMAP_Server: {imap_server}}}>"
		if smtp_login==None:smtp_login=login
		if imap_login==None:imap_login=login
		self.smtp_client=smtplib.SMTP(smtp_server)
		self.smtp_client.starttls()
		try:
			self.smtp_client.login(*smtp_login)
			self.smtp_client.ehlo_or_helo_if_needed()
		except smtplib.SMTPAuthenticationError:
			warn(SMTPAuthenticationError("!!!Warning!!! SMTP Authentication Not Accepted. Possible Causes:\n\t-Wrong Login Credentials.\n\t-Third Party Access Not Enabled.\n\t-Server Details Are Wrong.\nYou will not be able to use smtplib features such as sending mail."))
		self.imap_details=(imap_login,imap_server)
		self.imap_client=imaplib.IMAP4_SSL(imap_server)
		try:
			self.imap_client.login(*imap_login)
		except Exception:
			warn(IMAPLoginError("!!!Warning!!! IMAP Authentication Not Accepted. Possible Causes:\n\t-Wrong Login Credentials.\n\t-Third Party Access Not Enabled.\n\t-Server Details Are Wrong.\nYou will not be able to use imaplib features such as accessing mail."))

	def create_static(self,container):
		"""creates a static email object for threading and asynchronous processing"""
		return(Static_Client(self.imap_details,container,details=self.details))

	def _id_handle(self,email_id,client,count,tag):
		"""
		handles an email id to act similar to an array as an integer while strings are passed through
		"""
		try:
			if type(email_id)==int:
				if tag==None:
					email_id=range(count)[~email_id]
					email_id=[self._bytes(email_id)]
				else:
					email_id=[client.search(None,tag)[1][0].split()[~email_id]]

			if type(email_id)==str:
				if email_id.lower()=="all":
					if tag==None:
						email_id=list(range(count))
						email_id.reverse()
						email_id=list(map(self._bytes,email_id))
					else:
						email_id=client.search(None,tag)[1][0].split()
						email_id.reverse()

			if type(email_id)==list:
				gott=[]
				for eid in email_id:
					gott+=self._id_handle(eid,client,count,tag)

			return(self._list_return(email_id))
		except IndexError:
			raise(EmailIndexNotFound(f"Email Index {email_id} Not Found.")) from None

	def _container_handler(self,container):
		"""
		creates/handles a client and count of emails in a selected folder folder for easier use
		"""
		try:
			if type(container)==Static_Client:
				client=container
				count=container.count
			else:
				client=self.imap_client
				count=self._count(client.select(container),cont=container)
			return(client,count)
		except ValueError:
			raise(FolderNotFoundError(f"Folder \"{cont}\" Not Found.")) from None

	def _payload(self,message):
		"""
		extracts the main payload from the email headers
		"""
		if message.is_multipart():
			message_p=self._payload(message.get_payload(0))
		else:
			message_p=message.get_payload(None,True)
		return(message_p)

	def _attachments(self,message):
		"""
		extracts the attachments from the email headers
		"""
		files=[]
		for attachment in message.walk():
			if not (attachment.get_content_maintype()=="multipart" and attachment.get("Content-Disposition")==None):
				files.append(File(Name=attachment.get_filename(),Data=attachment.get_payload(decode=True)))
		return(files)

	def _extract(self,email_data):
		"""
		extracts attachments and body from the email's headers
		"""
		try:
			body=Body(self._payload(email_data).decode("utf-8"))
		except UnicodeDecodeError:
			body=Body("")
		attachments=self._attachments(email_data)
		header_dictionary=dict(email_data)
		email_found=Email(body,*attachments,**header_dictionary)
		return(email_found)

	def _count(self,selection,cont=None):
		"""a simplistic way of finding the number of emails in a container"""
		return(int(selection[1][0].decode("utf-8")))

	def noop(self):
		"""does a noop (no-operation)"""
		self.smtp_client.noop()
		self.imap_client.noop()

	def close(self):
		"""closes connections"""
		self.smtp_client.quit()
		self.imap_client.close()
		self.imap_client.logout()

	def send(self,Message,To=None,From=None):
		"""
		uses the smtp client to send a message
		"""
		if type(Message)==Email:
			if To==None:
				To=Message["To"]
			Message=Message.string()

		if From==None:From=self.email_adress
		try:
			self.smtp_client.sendmail(From,To,Message)
			return(True,"OK")
		except Exception as exception:
			return(False,exception)

	def folders(self):
		"""
		returns a list of names of folders/containers
		Note: 
		"""
		listings=[]
		for box in self.imap_client.list()[1]:
			box=box.decode().split(""" "/" """)
			listings.append((box[1][1:-1],box[0][1:-1]))
		return(listings)

	def get(self,container,email_id,tag=None):
		"""
		gets email headers from the email id and specialised tag
		"""
		client,count=self._container_handler(container)

		email_ids=self._id_handle(email_id,client,count,tag)

		end_emails=[]

		for email_id in email_ids:
			raw_data=client.fetch(email_id,"(RFC822)")
			if raw_data[0]!="OK":
				return(None)
			if raw_data[1][0]==None:
				raise(EmailIndexNotFound(f"Email Index {email_id} Not Found.")) from None

			raw_emails=[]
			new_emails=[]
			for email_val in range(0,len(raw_data[1]),2):
				raw_emails.append(raw_data[1][email_val][1])

			for raw_email in raw_emails:
				email_data=email.message_from_bytes(raw_email)
				new_emails.append(self._extract(email_data))

			end_emails+=new_emails
		return(end_emails)

	def emails_in(self,container,tag=None,id_list=False):
		"""
		Finds the email IDs/how many emails are in a container/folder
		"""
		client,count=self._container_handler(container)

		if tag==None:
			ids=list(range(count))
		else:
			all_ids=count
			ids=client.search(None,tag)[1][0].split()
			ids=[(all_ids-int(i)) for i in ids]
			ids.reverse()
		if id_list:
			return(ids)
		return(len(ids))

	def modify(self,container,email_id,mod,modification="+FLAGS",tag=None):
		"""
		adds/removes a tag to an email based off of an email id
		Note: "\\Deleted" deletes the email
		Note: "\\Trash" moves the email to the trash

		example:
			modify('"[Gmail]/All Mail"',"1:*","\\Trash",modification="+X-GM-LABELS")
			expunge('"[Gmail]/Trash"')
		"""
		client,count=self._container_handler(container)
		email_ids=self._id_handle(email_id,client,count,tag)
		for email_id in email_ids:
			client.store(email_id,modification,mod)

	def expunge(self,container):
		"""
		expunges a container
		"""
		client,count=self._container_handler(container)
		client.expunge()

	def await_email(self,container,count,timer=3,tag=None,debugging_function=lambda *args:None):
		"""
		a method that awaits for a container's new emails based on date checking. Native IMAP methods wern't too satisfactory so I cobbled one together with datetime, and time modules
		"""
		now=lambda:datetime.datetime.utcnow().replace(tzinfo=None)
		email_date=lambda new_email:datetime.datetime.strptime(" ".join((new_email["Date"]).split(" ")[:6]),"%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)

		counter=0

		previous_message_count=self.emails_in(container,tag=tag)
		now_time=now()
		prev_id=""
		while counter<count:
			time.sleep(timer)
			message_count=self.emails_in(container,tag=tag)
			if message_count!=previous_message_count:
				debugging_function(True)
				try:
					gotten_email=self.get(container,0,tag=tag)[0]
				except EmailIndexNotFound:
					continue
				if gotten_email["Message-ID"]!=prev_id:
					prev_id=gotten_email["Message-ID"]
					messages=[gotten_email]
					email_d=email_date(gotten_email)
					for email_id in range(1,message_count):
						gotten_email=self.get(container,email_id,tag=tag)[0]
						if email_date(gotten_email)>now_time:
							messages.append(gotten_email)
							continue
						break
					previous_message_count=message_count
					now_time=email_d
					for message in messages[:count-counter]:
						yield(message)
					counter+=len(messages)
			else:
				debugging_function(False)

	async def await_email_async(self,container,count,timer=3,tag=None,debugging_function=lambda *args:None):
		"""
		a method that awaits for a container's new emails based on date checking. Native IMAP methods wern't too satisfactory so I cobbled one together with datetime, and time modules
		"""
		now=lambda:datetime.datetime.utcnow().replace(tzinfo=None)
		email_date=lambda new_email:datetime.datetime.strptime(" ".join((new_email["Date"]).split(" ")[:6]),"%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)

		counter=0

		previous_message_count=self.emails_in(container,tag=tag)
		now_time=now()
		prev_id=""
		while counter<count:
			await asyncio.sleep(timer)
			message_count=self.emails_in(container,tag=tag)
			if message_count!=previous_message_count:
				debugging_function(True)
				try:
					gotten_email=self.get(container,0,tag=tag)[0]
				except EmailIndexNotFound:
					continue
				if gotten_email["Message-ID"]!=prev_id:
					prev_id=gotten_email["Message-ID"]
					messages=[gotten_email]
					email_d=email_date(gotten_email)
					for email_id in range(1,message_count):
						gotten_email=self.get(container,email_id,tag=tag)[0]
						if email_date(gotten_email)>now_time:
							messages.append(gotten_email)
							continue
						break
					previous_message_count=message_count
					now_time=email_d
					for message in messages[:count-counter]:
						yield(message)
					counter+=len(messages)
			else:
				debugging_function(False)

	def __repr__(self):
		"""provides a simplistic summary of the contents"""
		return(self.details)

	def __str__(self):
		"""provides a simplistic summary of the contents"""
		return(self.__repr__())