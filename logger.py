import datetime

class log_open:
	def __init__(self,*args,stdout=True,**kwargs):
		with open(args[0],"w") as file:
			file.write("")
		self.file=open(*args,"a+",**kwargs)
		self._reload=args,kwargs
		if stdout:
			self.out={print:([],{"end":""})}
		else:
			self.out={}

	def __getattr__(self,arg):
		return(getattr(self.file,arg))

	def save(self):
		self.file.close()
		self.file=open(*self._reload[0],"+a",**self._reload[1])

	def log(self,data,end="\n",formattation="[{0}] - {1}"):
		new_data=formattation.format(datetime.datetime.now(),data)+end
		self.file.write(new_data)
		for out in self.out:
			out(new_data,*self.out[out][0],**self.out[out][1])
		self.save()

	def new_output(self,func,*args,**kwargs):
		self.out[func]=(args,kwargs)

	def log_error(self,func):
		def new_func(*args,**kwargs):
			for attr in dir(func):
				try:
					setattr(new_func,attr,getattr(func,attr))
				except Exception:pass
			try:
				return(func(*args,**kwargs))
			except Exception as er:
				self.log(f"!!!Error in function \"{func.__name__}\"!!! Error: \"{str(er)}\"")
				self.save()
				raise er
		return(new_func)

	def log_call(self,func):
		def new_func(*args,**kwargs):
			for attr in dir(func):
				try:
					setattr(new_func,attr,getattr(func,attr))
				except Exception:pass
			self.log(f"Function {func.__name__} called")
			ret=func(*args,**kwargs)
			self.log(f"Function {func.__name__} ended")
			return(ret)
		return(new_func)