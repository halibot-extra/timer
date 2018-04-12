from halibot import HalModule
from datetime import timedelta
import time
import re
import uuid

regex = re.compile("(?:(\d+h))?(?:(\d+m))?(?:(\d+s))?")

# Parse the time setting string, and return a dictionary for timedelta kwargs
def parsetime(tup):
	ret = {}
	for i in tup:
		if not i:
			continue
		elif i[-1] == "h":
			ret["hours"] = int(i[:-1])
		elif i[-1] == "s":
			ret["seconds"] = int(i[:-1])
		elif i[-1] == "m":
			ret["minutes"] = int(i[:-1])

	if not ret.items():
		return None
	return ret


# Convert a string to a timedelta object
def get_timedelta(string):
	m = regex.match(string)
	if not m:
		return None

	timedict = parsetime(m.groups())
	if not timedict:
		return None

	return timedelta(**timedict)


# Get a random string to use as an ID
def get_randstring():
	return uuid.uuid4().hex[:6]

def tohuman(x):
	x = int(x)
	if x // 3600:
		return "{}h{}m{}s".format(x // 3600, (x % 3600) // 60, ((x % 3600) % 60))
	elif x // 60:
		return "{}m{}s".format(x // 60, x % 60)
	return "{}s".format(x)

class Timer(HalModule):

	def init(self):
		self.timers = {}
		self.watches = {}

	def error(self, msg, string):
		self.reply(msg, body="Timer failed: " + string)

	def sendmsg(self, msg, idstr, body):
		self.reply(msg, body=body)
		self.timers.pop(idstr)

	def queue_message(self, msg, secs, message):
			idstr = get_randstring()
			callback = self.eventloop.call_later(secs, self.sendmsg, *(msg, idstr, msg.author + ": " + message))
			self.timers[idstr] = callback
			return idstr

	def stopwatch(self, msg, mode, name):
		if mode == "start":
			self.watches[name] = time.time()
			self.reply(msg, body="Stopwatch '{}' started!".format(name))
		else:
			ret = self.watches.pop(name, None) if mode == "stop" else self.watches.get(name, None)
			if not ret:
				self.reply(msg, body="No watch named '{}' was started...".format(name))
				return
			self.reply(msg, body="Time elapsed for '{}': {}".format(name, tohuman(time.time() - ret)))

	def receive(self, msg):
		if not msg.body.startswith("!timer "):
			return

		try:
			cmd, tstring, message = msg.body.split(" ",2)
		except Exception as e:
			self.error(msg, str(e))
			return

		if tstring in ("cancel", "delete"):
			if message in self.timers:
				self.timers.pop(message).cancel()
				self.reply(msg, body="Timer '{}' cancelled".format(message))
			else:
				self.reply(msg, body="Timer '{}' not found!".format(message))
			return
		elif tstring in ("start","stop","check"):
			if not message:
				self.reply(msg, body="Need a stopwatch name!")
				return
			self.stopwatch(msg, tstring, message)
			return
		elif tstring in ("at"):
			self.reply(msg, body="This is not yet supported")
			return
			try:
				tstring, message = message.split(" ",1)
				self.abstime(msg, tstring, message)
			except Exception as e:
				self.reply(msg, body="Error setting timer: {}".format(e))
			return

		td = get_timedelta(tstring)
		if not td:
			self.error(msg, "Could not parse time string")
			return

		secs = int(td.total_seconds())
		idstr = ""
		try:
			idstr = self.queue_message(msg, secs, message)
		except Exception as e:
			self.error(msg, str(e))
			return

		self.reply(msg, body="Timer '{}' set for {} seconds from now".format(idstr, secs))

