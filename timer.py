from halibot import HalModule
from datetime import timedelta
import re

regex = re.compile("(?:(\d+h))?(?:(\d+m))?(?:(\d+s))?")

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
	return ret

	
def sendmsg(bot, msg, body):
	bot.reply(msg, body=body)

class Timer(HalModule):

	def init(self):
		pass

	def receive(self, msg):
		if not msg.body.startswith("!timer "):
			return None
		string, args = msg.body.split(" ",1)
		string, args = args.split(" ",1)
		m = regex.match(string)
		if not m:
			self.reply(msg, body="Timer failed: Could not parse time string")
			return

		secs = 0
		try:
			secs = int(timedelta(**parsetime(m.groups())).total_seconds())
			self.eventloop.call_later(secs, sendmsg, *(self, msg, msg.author + ": " + args))
		except Exception as e:
			self.reply(msg, body="Timer failed: {}".format(str(e)))
			return

		self.reply(msg, body="Timer set for {} seconds from now".format(secs))
