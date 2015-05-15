#!/usr/bin/python
"""
script to quickly test an openstack installation
based on api info found at http://www.ibm.com/developerworks/cloud/library/cl-openstack-pythonapis/
"""

import multiprocessing
import optparse
import os
from prettytable import PrettyTable
import sys
import time
import keystoneclient.v2_0.client as keystoneclient
import glanceclient.v2.client as glanceclient

__author__     = 'Karim Boumedhel'
__credits__    = ['Karim Boumedhel']
__license__    = 'GPL'
__version__    = '0.1'
__maintainer__ = 'Karim Boumedhel'
__email__      = 'karim.boumedhel@gmail.com'
__status__     = 'Testing'


keystonedefaulttests   = ['Create_Tenant', 'Create_User', 'Create_Role', 'Add_Role', 'ListRole', 'Authenticate_User', 'Delete_User', 'Delete_Role', 'Delete_Tenant']
glancedefaulttests   = ['Create_Image','List_Image','Delete_Image']
cinderdefaulttests   = ['Create_Volume','List_Volume','Delete_Volume']

def _keystonecreds():
	keystoneinfo                = {}
	keystoneinfo['username']    = os.environ['OS_USERNAME']
	keystoneinfo['password']    = os.environ['OS_PASSWORD']
	keystoneinfo['auth_url']    = os.environ['OS_AUTH_URL']
	keystoneinfo['tenant_name'] = os.environ['OS_TENANT_NAME']
	return keystoneinfo

def _novacreds():
	novainfo               = {}
	novainfo['username']   = os.environ['OS_USERNAME']
	novainfo['api_key']    = os.environ['OS_PASSWORD']
	novainfo['auth_url']   = os.environ['OS_AUTH_URL']
	novainfo['project_id'] = os.environ['OS_TENANT_NAME']
	return novainfo

def metrics(key):
	if not os.environ.has_key(key) or not ':' in os.environ[key] or not len(os.environ[key].split(':')) == 2  or not os.environ[key].replace(':','').isdigit():
		return 1,1
	else:
		concurrency = int(os.environ[key].split(':')[0])
		repeat = int(os.environ[key].split(':')[1])
 		return concurrency, repeat


class Openstuck():
	def __init__(self, keystonecredentials, novacredentials, endpoint, tenant='acmetenant', user='acmeuser', password='acmepassword', role='acmerole', email='acme@xxx.com', description='Members of the ACME Group', image='acmeimage', imagepath=None, volume='acmevolume', volumetype=None, debug=False,verbose=False):
		self.auth_url    = keystonecredentials['auth_url']
		self.novacreds   = novacredentials
		self.debug       = debug
		try:
			self.keystone    = keystoneclient.Client(**keystonecredentials)
		except:
			print "Issue making initial connection to keystone.Leaving"
			os._exit(1)
			keystoneclient.openstack.common.apiclient.exceptions.AuthorizationFailure
		self.output      = PrettyTable(['Category', 'Description', 'Concurrency', 'Repeat', 'Time(Seconds)', 'Result'])
		self.output.align['Category'] = "l"
		self.endpoint    = endpoint
		self.tenant      = tenant
		self.user        = user
		self.password    = password
		self.role 	 = role
		self.email       = email
		self.description = description
		self.image       = image
		self.imagepath   = imagepath
		self.volume      = volume
		self.volumetype  = volumetype
		self.debug       = debug
		self.verbose     = verbose
	def _first(self, elements):
		for element in elements:
			if element is not None:
				return element
		return None
	def _process(self, jobs):
		for j in jobs:
                	j.start()
		for j in jobs:
			j.join()
	def _addrows(self, verbose, rows):
		if not verbose or len(rows) == 0:
			return
		for row in rows:
			self.output.add_row(row)
	def _report(self, category, test, concurrency, repeat, time, errors):
		if test in errors:
			self.output.add_row([category, test, concurrency, repeat,'', "Failures: %d" % errors.count(test)])
		else:
			self.output.add_row([category, test, concurrency, repeat,time, 'OK'])
	def Add_Role(self, keystone, user, role, tenant, errors=None, output=None, verbose=False):
		starttime = time.time()
		if tenant is None or user is None:
			errors.append('Add_Role')
			results = 'NotRun'
			if verbose:
				print "Add_Role: %s to %s 0 seconds" % ('N/A', 'N/A')
				output.append(['keystone', 'Add_Role', 'N/A', 'N/A', '0', results,])
			return
		try:
			keystone.roles.add_user_role(user, role, tenant)
			results = 'OK'
		except Exception as error:
			errors.append('Add_Role')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Add_Role: %s to %s %s seconds" % (role.name, user.name, runningtime)
			output.append(['keystone', 'Add_Role', role.name, role.name, runningtime, results,])
	def Authenticate_User(self, user, password, auth_url, tenant=None, errors=None, output=None, verbose=False):
		starttime = time.time()
		if user is None or tenant is None:
			errors.append('Authenticate_User')
			results = 'NotRun'
			if verbose:
				print "Authenticate_User: %s in %s 0 seconds" % ('N/A', 'N/A')
				output.append(['keystone', 'Authenticate_User', 'N/A', 'N/A', '0', results,])
			return
		try:
			usercredentials = { 'username' : user.name, 'password' : password, 'auth_url' : auth_url , 'tenant_name' : tenant.name }
			userkeystone = keystoneclient.Client(**usercredentials)
			results = 'OK'
		except Exception as error:
			errors.append('Authenticate_User')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "Authenticate_User: %s in %s %s seconds" % (user.name, tenant.name, runningtime)
			output.append(['keystone', 'Authenticate_User', user.name, user.name, runningtime, results,])
	def Create_Image(self, glance, image, imagepath, images=None, errors=None, output=None, verbose=False):
		starttime = time.time()
		if imagepath is None:
			errors.append('Create_Image')
			results = 'Missing OS_GLANCE_IMAGE_PATH Environment variable for path'
			images.append(None)
			if verbose:
				print "Create_Image: %s" % 'N/A'
				output.append(['glance', 'Create_Image', 'N/A', 'N/A', '0', results,])
			return
		try:
			with open(imagepath,'rb') as data:
                        	newimage = glance.images.create(name=image, visibility='public', disk_format='qcow2',container_format='bare')
                        	glance.images.upload(newimage.id, data)
			results = 'OK'
			images.append(newimage.id)
		except Exception as error:
			errors.append('Create_Image')
			results = error
			images.append(None)
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Create_Image: %s %s seconds" % (image, runningtime )
			output.append(['glance', 'Create_Image', image, image, runningtime, results,])
	def Create_Role(self, keystone, name, roles=None, errors=None, output=None, verbose=False):
		starttime = time.time()
		try:
			role = keystone.roles.create(name=name)
			results = 'OK'
			roles.append(role.id)
		except Exception as error:
			errors.append('Create_Role')
			results = error
			roles.append(None)
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "Create_Role: %s %s seconds" % (name, runningtime)
			output.append(['keystone', 'Create_Role', name, name, runningtime, results,])
	def Create_Tenant(self, keystone, name, description, tenants=None, errors=None, output=None, verbose=False):
		starttime = time.time()
		try:
			tenant = keystone.tenants.create(tenant_name=name, description=description,enabled=True)
			results = 'OK'
			tenants.append(tenant.id)
		except Exception as error:
			errors.append('Create_Tenant')
			results = error
			tenants.append(None)
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Create_Tenant:%s %s seconds" % (name, runningtime)
			output.append(['keystone', 'Create_Tenant', name, name, runningtime, results,])
	def Create_User(self, keystone, name, password, email,tenant, users=None, errors=None, output=None, verbose=False):
		starttime = time.time()
		if tenant is None:
			errors.append('Create_User')
			results = 'NotRun'
			users.append(None)
			if verbose:
				print "Create_User: %s 0 seconds" % 'N/A'
				output.append(['keystone', 'Create_User', 'N/A', 'N/A', '0', results,])
			return
		try:
			user = keystone.users.create(name=name, password=password, email=email, tenant_id=tenant.id)
			results = 'OK'
			users.append(user.id)
		except Exception as error:
			errors.append('Create_User')
			results = error
			users.append(None)
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Create_User: %s %s seconds" % (name, runningtime)
			output.append(['keystone', 'Create_User', name, name, runningtime, results,])
	def Delete_Image(self, glance, image, errors=None, output=None, verbose=False):
		starttime = time.time()
		if image is None:
			errors.append('Delete_Image')
			results = 'NotRun'
			if verbose:
				print "Delete_Image: %s 0 seconds" % 'N/A'
				output.append(['glance', 'Delete_Image', 'N/A', 'N/A', '0', results,])
			return
		imagename = image.name
		try:
			glance.images.delete(image.id)
			results = 'OK'
		except Exception as error:
			errors.append('Delete_Image')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "Delete_Image: %s %s seconds" % (imagename, runningtime)
			output.append(['glance', 'Delete_Image', imagename, imagename, runningtime, results,])
	def Delete_Role(self, keystone, role, errors=None, output=None, verbose=False):
		starttime = time.time()
		if role is None:
			results = 'NotRun'
			if verbose:
				print "Delete_Role: %s 0 seconds" % 'N/A'
				output.append(['keystone', 'Delete_Role', 'N/A', 'N/A', '0', results,])
			return
		rolename = role.name
		try:
			role.delete()
			results = 'OK'
		except Exception as error:
			errors.append('Delete_Role')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "Delete_Role: %s %s seconds" % (rolename, runningtime)
			output.append(['keystone', 'Delete_Role', rolename, rolename, runningtime, results,])
	def Delete_Tenant(self, keystone, tenant, errors=None, output=None, verbose=False):
		starttime = time.time()
		if tenant is None:
			errors.append('Delete_Tenant')
			results = 'NotRun'
			if verbose:
				print "Delete_Tenant: %s 0 seconds" % 'N/A'
				output.append(['keystone', 'Delete_Tenant', 'N/A', 'N/A', '0', results,])
			return
		tenantname = tenant.name
		try:
			tenant.delete()
			results = 'OK'
		except Exception as error:
			errors.append('Delete_Tenant')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Delete_Tenant: %s %s seconds" % (tenantname, runningtime)
			output.append(['keystone', 'Delete_Tenant', tenantname, tenantname, runningtime, results,])
	def Delete_User(self, keystone, user, errors=None, output=None, verbose=False):
		starttime = time.time()
		if user is None:
			results = 'NotRun'
			errors.append('Delete_User')
			if verbose:
				print "Delete_User: %s 0 seconds" % 'N/A'
				output.append(['keystone', 'Delete_User', 'N/A', 'N/A', '0', results,])
			return
		username = user.name
		try:
			user.delete()
			results = 'OK'
		except Exception as error:
			errors.append('Delete_User')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime) 
			print "Delete_User: %s %s seconds" % (username, runningtime)
			output.append(['keystone', 'Delete_User', username, username, runningtime, results,])
	def List_Image(self, glance, image, errors=None, output=None, verbose=False):
		starttime = time.time()
		if image is None:
			results = 'NotRun'
			errors.append('List_Image')
			if verbose:
				print "List_Image: %s 0 seconds" % 'N/A'
				output.append(['glance', 'List_Image', 'N/A', 'N/A', '0', results,])
			return
		try:
			glance.images.get(image.id)
			results = 'OK'
		except Exception as error:
			errors.append('List_Image')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "List_Image: %s %s seconds" % (image.name, runningtime)
			output.append(['glance', 'List_Image', image.name, image.name, runningtime, results,])
	def List_Role(self, keystone, role, errors=None, output=None, verbose=False):
		starttime = time.time()
		if role is None:
			results = 'NotRun'
			errors.append('List_Role')
			if verbose:
				print "List_Role: %s" % 'N/A'
				output.append(['keystone', 'List_Role', 'N/A', 'N/A', '0', results,])
			return
		try:
			keystone.roles.get(role.id)
			results = 'OK'
		except Exception as error:
			errors.append('List_Role')
			results = error
		if verbose:
			endtime     = time.time()
			runningtime = "%0.3f" % (endtime -starttime)
			print "List_Role: %s %s seconds" % (role.name, runningtime)
			output.append(['keystone', 'List_Role', role.name, role.name, runningtime, results,])
	def _printreport(self):
		return self.output
	def listservices(self):
		keystone = self.keystone
		output = PrettyTable(['Service', 'Type', 'Status'])
		output.align['Service'] = "l"
		for service in sorted(keystone.services.list(), key = lambda s: s.name):
			status = 'Available' if service.enabled else 'N/A'
			output.add_row([service.name, service.type, status])
		return output
	def keystoneclean(self, tenants, users, roles):
		if self.verbose:
			print "Cleaning Keystone..."
		keystone = self.keystone
		for tenant in tenants:
			if tenant is None:
				continue
			else:
				try :
					tenant.delete()	
				except:
					continue
		for user in users:
			if user is None:
				continue
			else:
				try:
					user.delete()
				except:
					continue
		for role in roles:
			if role is None:
				continue
			else:
				try:
					role.delete()
				except:
					continue
	def glanceclean(self, image):
#		try:
#			print "Cleaning Glance..."
#			for img in glance.images.list():
#				if img['name'] == image:
#					glance.images.delete(img['id'])
#		except:
#			pass

		if self.verbose:
			print "Cleaning Glance..."
		keystone = self.keystone
		endpoint = keystone.service_catalog.url_for(service_type='image',endpoint_type=self.endpoint)
		glance = glance.Client(endpoint, token=keystone.auth_token)
		for image in images:
			if image is None:
				continue
			else:
				try:
					glance.images.delete(image.id)
				except:
					continue
	def cinderclean(self, volumes):
		if self.verbose:
			print "Cleaning Cinder..."
		keystone = self.keystone
		endpoint = keystone.service_catalog.url_for(service_type='volume',endpoint_type=self.endpoint)
		cinder = cinderclient.Client(endpoint, token=keystone.auth_token)
		for volume in volumes:
			if volume is None:
				continue
			else:
				try:
					cinder.volumes.delete(volume.id)
				except:
					continue
	def keystonetest(self):
		category = 'keystone'
		mgr = multiprocessing.Manager()
		tenants = mgr.list()
		users   = mgr.list()
		roles   = mgr.list()
		errors  = mgr.list()
		if self.verbose:
			print "Testing Keystone..."
		keystone = self.keystone

                test   = 'Create_Tenant'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		for step in range(repeat):
			jobs = [ multiprocessing.Process(target=self.Create_Tenant, args=(keystone, "%s-%d-%d" % (self.tenant, step,number), self.description, tenants, errors, output, self.verbose,)) for number in range(concurrency) ]
			self._process(jobs)
		endtime    = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)
		tenants = [ keystone.tenants.get(tenant_id) if tenant_id is not None else None for tenant_id in tenants]

	        test   = 'Create_User'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		for step in range(repeat):
			jobs = [ multiprocessing.Process(target=self.Create_User, args=(keystone, "%s-%d-%d" % (self.user, step, number), self.password, self.email, self._first(tenants), users, errors, output, self.verbose,)) for number in range(concurrency) ]
			self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)
		users = [ keystone.users.get(user_id) if user_id is not None else None for user_id in users ]

	        test   = 'Create_Role'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		for step in range(repeat):
			jobs = [ multiprocessing.Process(target=self.Create_Role, args=(keystone, "%s-%d-%d" % (self.role, step, number), roles, errors, output, self.verbose, )) for number in range(concurrency) ]
			self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)
		roles = [ keystone.roles.get(role_id) if role_id is not None else None for role_id in roles ]

	        test   = 'Add_Role'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Add_Role, args=(keystone, self._first(users), role, self._first(tenants), errors, output, self.verbose, )) for role in roles ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

	        test   = 'List_Role'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.List_Role, args=(keystone, role, errors, output, self.verbose, )) for role in roles ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

	        test   = 'Authenticate_User'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Authenticate_User, args=(user, self.password, self.auth_url, self._first(tenants), errors, output, self.verbose, )) for user in users ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		test   = 'Delete_User'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Delete_User, args=(keystone, user, errors, output, self.verbose, )) for user in users ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		test   = 'Delete_Role'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Delete_Role, args=(keystone, role, errors, output, self.verbose, )) for role in roles ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		test   = 'Delete_Tenant'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Delete_Tenant, args=(keystone, tenant, errors, output, self.verbose, )) for tenant in tenants ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		self.keystoneclean(tenants, users, roles)

	def glancetest(self):
		category = 'glance'
		mgr = multiprocessing.Manager()
		errors  = mgr.list()
		images = mgr.list()
		if self.verbose:
			print "Testing Glance..."
		keystone = self.keystone
		endpoint = keystone.service_catalog.url_for(service_type='image',endpoint_type=self.endpoint)
		glance = glanceclient.Client(endpoint, token=keystone.auth_token)

                test = 'Create_Image'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		for step in range(repeat):
			jobs = [ multiprocessing.Process(target=self.Create_Image, args=(glance, "%s-%d-%d" % (self.image, step, number), self.imagepath, images, errors, output, self.verbose, )) for number in range(concurrency) ]
			self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)
		images = [ glance.images.get(image_id) if image_id is not None else None for image_id in images ]

                test = 'List_Image'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.List_Image, args=(glance, image, errors, output, self.verbose, )) for image in images ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

                test = 'Delete_Image'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Delete_Image, args=(glance, image, errors, output, self.verbose, )) for image in images ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		self.glanceclean(images)
	def cindertest(self):
		category = 'cinder'
		mgr = multiprocessing.Manager()
		errors  = mgr.list()
		volumes = mgr.list()
		if self.verbose:
			print "Testing Cinder..."
		keystone = self.keystone
		endpoint = keystone.service_catalog.url_for(service_type='volume',endpoint_type=self.endpoint)
		cinder = cinderclient.Client(endpoint, token=keystone.auth_token)

                test = 'Create_volume'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		for step in range(repeat):
			jobs = [ multiprocessing.Process(target=self.Create_Volume, args=(cinder, "%s-%d-%d" % (self.volume, step, number), self.volumetype, volumes, errors, output, self.verbose, )) for number in range(concurrency) ]
			self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)
		volumes = [ cinder.volumes.get(volume_id) if volume_id is not None else None for volume_id in volumes ]

                test = 'List_Volumes'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.List_Volume, args=(cinder, volume, errors, output, self.verbose, )) for volume in volumes ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

                test = 'Delete_Volume'
		output = mgr.list()
                concurrency, repeat = metrics(test)
		starttime = time.time()
		jobs = [ multiprocessing.Process(target=self.Delete_Volume, args=(glance, volume, errors, output, self.verbose, )) for volume in volume ]
		self._process(jobs)
		endtime = time.time()
		runningtime = "%0.3f" % (endtime -starttime)
		if verbose:
			print "%s  %s seconds" % (test, runningtime)
		self._report(category, test, concurrency, repeat, runningtime, errors)
		self._addrows(verbose, output)

		self.cinderclean(volumes)
	
if __name__ == "__main__":
	#parse options
	usage   = "test openstack installation quickly"
	version = "0.1"
	parser  = optparse.OptionParser("Usage: %prog [options] deployment",version=version)
	listinggroup = optparse.OptionGroup(parser, 'Listing options')
	listinggroup.add_option('-l', '--listservices', dest='listservices', action='store_true', help='List available services')
	parser.add_option_group(listinggroup)
	testinggroup = optparse.OptionGroup(parser, 'Testing options')
	testinggroup.add_option('-A', '--availability', dest='testha', action='store_true',default=False, help='Test High Availability')
	testinggroup.add_option('-C', '--cinder', dest='testcinder', action='store_true',default=False, help='Test cinder')
	testinggroup.add_option('-E', '--all', dest='testall', action='store_true',default=False, help='Test All')
	testinggroup.add_option('-G', '--glance', dest='testglance', action='store_true',default=False, help='Test glance')
	testinggroup.add_option('-H', '--heat', dest='testheat', action='store_true',default=False, help='Test heat')
	testinggroup.add_option('-K', '--keystone', dest='testkeystone', action='store_true',default=False, help='Test keystone')
	testinggroup.add_option('-N', '--nova', dest='testnova', action='store_true',default=False, help='Test neutron')
	testinggroup.add_option('-Q', '--neutron', dest='testneutron', action='store_true',default=False, help='Test neutron')
	testinggroup.add_option('-S', '--swift', dest='testswift', action='store_true',default=False, help='Test swift')
	parser.add_option_group(testinggroup)
	parser.add_option('-p', '--project', dest='project', default='acme', type='string', help='Project name to prefix for all elements. defaults to acme')
	parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true', help='Verbose mode')
	(options, args) = parser.parse_args()
	listservices    = options.listservices
	testkeystone    = options.testkeystone
	testglance      = options.testglance
	testcinder      = options.testcinder
	testneutron     = options.testneutron
	testnova        = options.testnova
	testheat        = options.testheat
	testswift       = options.testswift
	testha          = options.testha
	testall         = options.testall
	project         = options.project
	verbose         = options.verbose
	user               = "%suser" % project
	password           = "%spassword" % project
	role               = "%srole" % project
	tenant             = "%stenant" % project
	email              = "%suser@xxx.com" % project
	description        = "Members of the %s corp" % project
	image              = "%simage" % project
	try:
		keystonecredentials = _keystonecreds()
		novacredentials     = _novacreds()
		endpoint            = os.environ['OS_ENDPOINT_TYPE'] if os.environ.has_key('OS_ENDPOINT_TYPE') else 'publicURL'
		keystonetests       = os.environ['OS_KEYSTONETESTS'] if os.environ.has_key('OS_KEYSTONETESTS') else keystonedefaulttests
		glancetests         = os.environ['OS_GLANCETESTS'] if os.environ.has_key('OS_GLANCETESTS') else glancedefaulttests
		imagepath           = os.environ['OS_GLANCE_IMAGE_PATH'] if os.environ.has_key('OS_GLANCE_IMAGE_PATH') else None
	except:
		print "Missing environment variables. source your openrc file first"
	    	os._exit(1)

	o = Openstuck(keystonecredentials=keystonecredentials, novacredentials=novacredentials, endpoint=endpoint, tenant=tenant, user=user, password=password, role=role, email=email, description=description, image=image, imagepath=imagepath, verbose=verbose)
	
	if listservices:
		print o.listservices()
	    	sys.exit(0)
	if testkeystone or testall:
		o.keystonetest()
	if testglance or testall:
		o.glancetest()
	if testcinder or testall:
		o.cindertest()
	if testneutron or testall:
		o.neutrontest()
	if testnova or testall:
		o.novatest()
	if testheat or testall:
		o.heattest()
	if testswift or testall:
		o.swifttest()
	if testha or testall:
		o.alltest()
	if testkeystone or testglance or testcinder or testneutron or testnova or testheat or testswift or testha or testall:
		if verbose:
			print "Testing Keystone..."
			print "Final report:"
		print o._printreport()
