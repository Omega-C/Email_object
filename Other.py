import numpy as _numpy
from random import randint as _randint

__author__="Spencer Rumbaugh of Planck Solutions INC.\nGitHub:Omega-C"

#credit to Ricky for the idea

"""
TODO (DO IN ORDER):

-work on convolutional cells, 2D and 3D (3D supports 2D so 3D reccomended only)
-work on support for RNN backpropigation through time, possible other network but attempt to implement that in default, !NEED MAJOR REVAMPS IN RNN CELL CLASS!
x-Implement overflow catching as optional
-Implement error types and basic quality of life stuff, maybe a class for activations and a class for derived cells. This is not neccecary if not wanted.
-optimise further
-finish unfinished things

-try in java?
-try functionally as it may save time.
"""

"""global interchangable variables"""
matrix_dtype=None
seterr=_numpy.seterr
seterr(over="ignore")

"""Built In Functions"""
def dtype(name):
	"""numpy dtype creator"""
	return(_numpy.dtype(name))

def To_List(matrix,*args,**kwargs):
	"""converts a matrix to a list"""
	return(matrix.tolist(*args,**kwargs))

def To_Matrix(lis,*args,**kwargs):
	"""converts a list to a matrix"""
	kwargs.setdefault("dtype",matrix_dtype)
	return(_numpy.array(lis,*args,**kwargs))

def Add_Matrix(matrix1,matrix2):
	"""adds matricies together bacsed on collumns"""
	return(_numpy.append(matrix1,matrix2,axis=1))

def Sum_Matricies(matricies):
	"""adds matricies in a list"""
	base=matricies[0]
	for matrix in matricies[1:]:
		base=Add_Matrix(base,matrix)
	return(base)

def Random_Matrix(*args):
	"""creates a randomised matrix"""
	return(2*_numpy.random.random(args)-1)

def Roll_Random(maximum=1E+8):
	"""creates a random seed"""
	_numpy.random.seed(_randint(1,maximum))

def label(lis,labels):
	"""labels a list of datasets with a list of labels"""
	su=0
	for val in lis: su+=val
	maximum=max(lis)
	confidence=100*maximum/su
	for num, val in enumerate(lis):
		if val==maximum:
			return(labels[num],confidence)


"""Activation functions"""
def softmax(x):#need prime
	exp=_numpy.exp(x-x.max(axis=1)[:,_numpy.newaxis])
	return(exp/exp.sum(axis=1)[:,_numpy.newaxis])

def sig(x):
	return(1/(1+_numpy.exp(-x)))

def tanh(x):
	return(_numpy.tanh(x))

def sig_prime(x):
	return(sig(x)*(1-sig(x)))

def tanh_prime(x):
	return(4*sig_prime(2*x))

def ReLU(x):
	return(_numpy.where(x>0,x,0))

def ReLU_prime(x):
	return(_numpy.where(x>0,1,0))

def LReLU(x,a=0.2):
	return(_numpy.where(x>0,x,a*x))

def LReLU_prime(x,a=0.2):
	return(_numpy.where(x>0,1,a))

def ELU(x,a=0.2):
	return(_numpy.where(x>0,x,a*(_numpy.exp(x)-1)))

def ELU_prime(x,a=0.2):
	return(_numpy.where(x>0,1,ELU(x)+1))

def SELU(x,a=1.673263242354377284,g=1.050700987355480493):
	return(g*_numpy.where(x>0,x,a*_numpy.exp(x)-a))

def SELU_prime(x,a=1.673263242354377284,g=1.050700987355480493):
	return(g*_numpy.where(x>0,1,a*_numpy.exp(x)))

#parametric_relu comming soon

def swish(x):
	return(_numpy.multiply(x,sig(x)))

def swish_prime(x):
	return(_numpy.divide(_numpy.multiply(_numpy.exp(x),(x+_numpy.exp(x)+1)),_numpy.multiply((_numpy.exp(x)+1),(_numpy.exp(x)+1))))


"""Built In Classes"""
class Layer:
	def __init__(self,cell,*dims,**kwargs):
		"""a base layer type that includes modification of weights based on given cell functions"""
		if type(cell)==type:
			cell=cell()
			if not issubclass(cell.__class__,Cell):
				raise(TypeError("The cell given is not a usable cell"))
		else:
			if not issubclass(cell.__class__,Cell):
				raise(TypeError("The cell given is not a usable cell"))
		self.cell=cell
		self.weights=Random_Matrix(*dims)
		kwargs.setdefault("dtype",matrix_dtype)
		if kwargs["dtype"]!=None:
			self.weights=self.weights.astype(kwargs["dtype"])

	def __repr__(self):
		return(f"Layer[{str(self.cell)}:Weight_Matrix[{len(self.weights)}->{len(self.weights[0])}]]")

	def forward_propigate(self,previous):
		return(self.cell.feed_forward(previous,self.weights))

	def back_propigate_last(self,err_n,layer_p):
		der_n=err_n*self.cell.prime(layer_p)
		return(der_n)

	def back_propigate(self,err,layer_p,der,l2):
		err_n=der.dot(l2.weights.T)
		der_n=err_n*self.cell.prime(layer_p)
		return(err_n,der_n)

	def configure_weights(self,rate,layer,derivative):
		self.weights-=(rate*layer.T.dot(derivative))

	def from_list(lis,*args,**kwargs):
		ret=[]
		for argsm in lis:
			ret.append(Layer(*argsm,*args,**kwargs))
		return(ret)

class Network:
	def __init__(self,*layers):
		"""a base Network comprised of Layers, utilises layer methods to combind multiple network types, activations, etc"""
		if len(layers)==0:
			return(None)
		if type(layers[0])==list or type(layers[0])==tuple:
			layers=layers[0]
		self.layers=layers

	def forward_propigate(self,inp):
		layers=[inp]
		for layer in self.layers:
			layers.append(layer.forward_propigate(layers[-1]))
		return(layers)

	def back_propigate(self,layers,out):
		layers=layers.copy()
		errors=[layers[-1]-out]
		derivatives=[]
		derivatives.append(self.layers[-1].back_propigate_last(errors[0],layers[-1]))
		for l in range(1,len(layers)-1):
			err,der=self.layers[~l].back_propigate(errors[-1],layers[~l],derivatives[-1],self.layers[-l])
			errors.append(err);derivatives.append(der)
		return(errors,derivatives)

	def configure_weights(self,rate,derivatives,layers):
		for i in range(len(self.layers)):
			self.layers[i].configure_weights(rate,layers[i],derivatives[~i])

	def train(self,inp,out,rate=0.05,respond=False):
		layers=self.forward_propigate(inp)
		errors,derivatives=self.back_propigate(layers,out)
		self.configure_weights(rate,derivatives,layers)
		if respond:
			return(errors)

	def save(self,file,*pklargs,**pklkwargs):
		"""saves layers to a .pickle file"""
		with open(file,"wb") as f:
			_numpy.save(f,self.__dict__,*pklargs,**pklkwargs)

	def load(self,file,*pklargs,**pklkwargs):
		"""loads layers from a .pickle file"""
		with open(file,"rb") as f:
			gotten=_numpy.load(f,allow_pickle=True,*pklargs,**pklkwargs)
		self.__dict__.update(gotten.item())


"""Cells"""
class Cell:
	def __init__(self,*args,**kwargs):
		"""a base cell that is used to identify if a layer can be used"""
		pass

	def activate(self,weights):
		"""activation function"""
		return(weights)

	def prime(self,weights):
		"""prime of activation function"""
		return(weights)

	def feed_forward(self,previous,weights):
		"""feeds forward using the activation function"""
		return(self.activate(_numpy.dot(previous,weights)))

	def __repr__(self):
		return(f"{self.__class__.__name__}")

class Set_Cell(Cell):
	def __init__(self,value=1):
		"""a Cell object that always returns the value set in forward propigation"""
		self.value=value

	def feed_forward(self,previous,weights):
		return(To_Matrix([[self.value] for _ in range(len(previous))]))

class Convolution_Cell(Cell):
	"""In Progress"""
	pass

class RNN_Cell(Cell):
	"""a Cell object that tries to utilise built in memory"""
	def __init__(self,activation=tanh,prime=tanh_prime):
		self.previous=0
		self.activation=activation
		self.prime_f=prime

	def activate(self,weights):
		result=self.activation(weights+self.previous)
		self.previous=result
		return(softmax(result))

	def prime(self,weights):
		return(self.prime_f(weights))

class Hidden_Cell(Cell):
	def __init__(self,activation=sig,prime=sig_prime):
		"""a base example of a cell. Using just the activation and prime functions of sigmoid"""
		self.activation=activation
		self.prime_f=prime

	def activate(self,weights):
		return(self.activation(weights))

	def prime(self,weights):
		return(self.prime_f(weights))


"""running a test"""
def _main():
	def label(lis,labels):
		"""labels a list of datasets with a list of labels"""
		su=0
		for val in lis: su+=val
		maximum=max(lis)
		confidence=100*maximum/su
		for num, val in enumerate(lis):
			if val==maximum:
				return(labels[num],confidence)
	import datetime
	ts0=datetime.datetime.now()
	global matrix_dtype
	matrix_dtype=dtype("float32")
	print("This is a test where the network will take the sum of all the 1s and mod that number by 2\nThe end result printed will be the results of all training, and the first displayed is the untrained result.\nThe network will refine over time as you will see\n")
	layers=Layer.from_list([
		(Hidden_Cell,3,6),
		(Hidden_Cell,6,1)
		])
	net=Network(layers)
	inp=To_Matrix([[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]])
	out=To_Matrix([[0],[1],[1],[0],[1],[0],[0],[1]])
	ts=0
	ran=500000
	iterator=10
	def do_stuff(ts):
		print(f"iteration: {ts}/{iterator}")
		output=net.forward_propigate(inp)[-1]
		results=["Accurate: "+{True:"Yes",False:"No"}[out[n][0]=={True:1,False:0}[l[0]>0.5]]+f"; Original Value: {out[n][0]}; Returned Value: {l[0]}; Error: {abs(l[0]-out[n][0])}" for n,l in enumerate(output)]
		print("\n".join(results))
		print("\n\n")
		ts+=1
		return(ts)
	ts1=datetime.datetime.now()
	for x in range(ran):
		if x%(ran//iterator)==0:
			ts=do_stuff(ts)
		net.train(inp,out,rate=1*(ran-x)/ran)
	ts=do_stuff(ts)
	ts2=datetime.datetime.now()
	print(f"setup time: {ts1-ts0}\nnetwork runtime: {ts2-ts1}\nfull runtime: {ts2-ts0}")

if __name__=="__main__":
	_main()