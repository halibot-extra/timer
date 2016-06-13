from halibot import HalModule
from datetime import timedelta
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

class Timer(HalModule):

	def init(self):
		self.timers = {}

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
