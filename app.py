from flask import Flask, render_template, redirect
import psutil
import json
import webview
import sys
import threading

app = Flask(__name__)

frequency = []
available = []
used = []
window = None
process_window = None

def get_size(bytes, suffix="B"):
	factor = 1024
	for unit in ["", "K", "M", "G", "T", "P"]:
		if bytes < factor:
			return f"{bytes:.2f}{unit}{suffix}"
		bytes /= factor

@app.route('/')
def index():
	svmem = psutil.virtual_memory()
	total = get_size(svmem.total)
	us = get_size(svmem.used)
	av = get_size(svmem.available)


	data = {
		"total": total,
		"used": us,
		"available": av
	}

	return render_template('index.html', **data)

@app.route('/ram_stats')
def ram_stats():
	"give ram stats every sec"
	svmem = psutil.virtual_memory()
	total = get_size(svmem.total)
	us = get_size(svmem.used)
	av = get_size(svmem.available)

	return f"Ram - Total {total}, Available - {av}, Used - {us}"


@app.route('/cpu')
def cpu():
	cpufreq = psutil.cpu_freq()
	global frequency
	frequency.append(cpufreq.current)

	if len(frequency) > 10:
		frequency = frequency[1:10]

	return json.dumps(frequency)

@app.route('/ram_av')
def ram():
	svmem = psutil.virtual_memory()
	global available

	global used
	used.append(svmem.used)

	available.append(svmem.available)
	

	if len(available) > 100:
		available = available[1:100]

	if len(used) > 100:
		used = used[1:100]

	return json.dumps([available, used])

@app.route('/ram_us')
def ram_us():
	svmem = psutil.virtual_memory()
	global used
	used.append(get_size(svmem.used))

	if len(used) > 10:
		used = used[1:10]

	return json.dumps(used)

def get_processes(kill=False, pid=None):
	proc_list = []

	for proc in psutil.process_iter():
		try:
			pinfo = proc.as_dict(attrs=["pid", "name", "memory_percent", "cpu_percent"])
			if pinfo['memory_percent'] > 0.25 and pinfo['cpu_percent'] > 0.25:
				try:
					if int(pinfo['pid']) == int(pid):
						proc.kill()
				except:
					proc_list.append(pinfo)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass
	if not kill:
		return proc_list

@app.route('/processes')
def processes():
	data = {
		"processes" : get_processes()
	}
	return render_template('processes.html', **data)

@app.route('/change_processes')
def change_proc():
	global window
	window.load_url("http://127.0.0.1:5000/processes")
	return redirect('/processes')

@app.route('/go_home')
def go_home():
	global window
	window.load_url("http://127.0.0.1:5000/")
	return ''

@app.route('/kill/<pid>')
def kill(pid):
	# for proc in psutil.process_iter():
	# 	try:
	# 		pinfo = proc.as_dict(attrs=["pid"])
	# 		print(pid == pinfo['pid'])
	# 		if pid == pinfo['pid']:
	# 			print(proc)
	# 			proc.kill()
	# 	except (psutil.NoSuchProcess, psutil.ZombieProcess):
	# 		pass
	# 	except psutil.AccessDenied:
	# 		print("AccessDenied")
	get_processes(kill=True, pid=pid)
	window.load_url("http://127.0.0.1:5000/processes")
	return ''


def start_server():
	app.run()

def change_processes():
	window.load_url('http://127.0.0.1:5000/processes')

if __name__ == "__main__":
	t = threading.Thread(target=start_server)
	t.daemon = True
	t.start()
	#global window
	window = webview.create_window("Task Manager", "http://127.0.0.1:5000/", confirm_close=True)
	#sys.exit()
	webview.start()
	sys.exit()
