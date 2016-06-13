from halibot import HalModule
from datetime import timedelta
import re

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

	
class Timer(HalModule):

	def init(self):
		pass

	def error(self, msg, string):
		self.reply(msg, body="Timer failed: " + string)

	def sendmsg(self, msg, body):
		self.reply(msg, body=body)

	def receive(self, msg):
		if not msg.body.startswith("!timer "):
			return

		try:
			cmd, tstring, message = msg.body.split(" ",2)
		except Exception as e:
			self.error(msg, str(e))
			return

		td = get_timedelta(tstring)
		if not td:
			self.error(msg, "Could not parse time string")
			return

		secs = int(td.total_seconds())
		try:
			self.eventloop.call_later(secs, self.sendmsg, *(msg, msg.author + ": " + message))
		except Exception as e:
			self.error(msg, str(e))
			return

		self.reply(msg, body="Timer set for {} seconds from now".format(secs))
