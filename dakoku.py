#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yuki Furuta <furushchev@jsk.imi.i.u-tokyo.ac.jp>


try:
    from splinter import Browser
    import pytz
    from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler
    from apscheduler.triggers.cron import CronTrigger
except Exception as e:
    print "Error:", e
    print "try:"
    print "\tsudo apt-get install python-pyside python-pip"
    print "\tsudo pip install -r pip.txt"
    exit(1)
import os
import shutil
import re
import datetime as dt
import json
import urllib2
from threading import Timer
from random import random

# logging
import logging
LEVEL = logging.INFO
log = logging.getLogger(__name__)
fmt = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setLevel(LEVEL)
handler.setFormatter(fmt)
log.setLevel(logging.DEBUG)
log.addHandler(handler)

def dispatch_after(time, callback):
    def func():
        t = Timer(random() * time, callback)
        t.start()
    return func

class DakokuWorker(object):
    def __init__(self, host, user, password, holidays, capture_dir=None):
        self.host = host
        self.user = user
        self.password = password
        self.holidays = holidays
        self.capture_dir = capture_dir

    def _is_same_day(self, t1, t2):
        return t1.strftime('%Y%m%d') == t2.strftime('%Y%m%d')

    def _is_holiday(self, t):
        for h in self.holidays:
            if self._is_same_day(t, h): return True
        return False

    def _login(self):
#        self.browser = Browser("phantomjs", user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36")
        self.browser = Browser("firefox")
        self.browser.visit(self.host)
        self.browser.fill('user_id', self.user)
        self.browser.fill('password', self.password)
        try:
            log.info("logging in: %s", self.browser.title.decode('utf-8'))
        except:
            log.info("logging in: %s", self.browser.title)

    def work_start(self):
        now_time = dt.datetime.now().replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        try:
            if self._is_holiday(now_time):
                log.info("Today is holiday! Skipping...")
                return
            self._login()
            if self.browser.is_element_present_by_name("syussya", wait_time=5):
                self.browser.find_by_name("syussya").click()
            else:
                log.error("failed to load web page")
                return
            log.info(now_time.strftime("work started at %Y-%m-%d %H:%M:%S"))
            if self.capture_dir:
                capture_path = os.path.join(self.capture_dir, now_time.strftime('syussya_%Y-%m-%d-%H:%M:%S.jpg'))
                tmppath = self.browser.screenshot(suffix="jpg")
                log.info("captured: %s", tmppath)
                shutil.copyfile(tmppath, capture_path)
                log.info("copied to: %s", capture_path)
        except Exception as e:
            log.error("failed to start work: %s", str(e))
        finally:
            self.browser.quit()

    def work_end(self):
        now_time = dt.datetime.now().replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        try:
            if self._is_holiday(now_time):
                log.info("Today is holiday! Skipping...")
                return
            self._login()
            if self.browser.is_element_present_by_name("taisya", wait_time=5):
                self.browser.find_by_name("taisya").click()
            else:
                log.error("failed to load web page")
                return
            log.info(now_time.strftime("work ended at %Y-%m-%d %H:%M:%S"))
            if self.capture_dir:
                capture_path = os.path.join(self.capture_dir, now_time.strftime('taisya_%Y-%m-%d-%H:%M:%S.jpg'))
                tmppath = self.browser.screenshot(suffix="jpg")
                log.info("captured: %s", tmppath)
                shutil.copyfile(tmppath, capture_path)
                log.info("copied to: %s", capture_path)
        except Exception as e:
            log.error('failed to end work: %s', str(e))
        finally:
            self.browser.quit()

class DakokuManager(object):
    def __init__(self, config_path, schedule_path):
        self.config_path = config_path
        self.schedule_path = schedule_path
        cfg = self._load_config()
        try:
            human_mode_min = cfg["human_mode"]
        except:
            human_mode_min = 0
        try:
            self.log_dir = cfg["log_dir"]
            file_handler = logging.FileHandler(os.path.join(self.log_dir, "dakoku.log"), 'a+')
            file_handler.level = LEVEL
            log.addHandler(file_handler)
            log.info("saving log to %s", self.log_dir)
        except:
            self.log_dir = None

        sched = self._load_schedule()
        start_date = dt.datetime.strptime(sched["valid"]["start"], '%Y-%m-%d').replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        end_date = dt.datetime.strptime(sched["valid"]["end"], '%Y-%m-%d').replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        log.info("dakoku is valid for %s - %s", start_date, end_date)
        holidays = self._get_holidays(start_date, end_date)
        self.worker = DakokuWorker(cfg["host"], cfg["user"], cfg["pass"], holidays, self.log_dir)
        self.register(sched["working"], start_date, end_date, holidays, human_mode_min)

    def _load_config(self):
        log.debug("loading config from %s", self.config_path)
        with open(self.config_path, 'r') as f:
            cfg = json.load(f)
        return cfg

    def _load_schedule(self):
        log.debug("loading schedule from %s", self.schedule_path)
        with open(self.schedule_path, 'r') as f:
            cfg = json.load(f)
        return cfg
        
    def _get_holidays(self, start_date, end_date):
        pattern = re.compile("^.*basic\/([0-9]*)_.*$")
        calendar_id = 'japanese__ja@holiday.calendar.google.com'
        calendar_host = 'https://www.google.com/calendar/feeds/'
        calendar_start = '/public/basic?start-min=' + start_date.strftime('%Y-%m-%d')
        calendar_end = '&start-max=' + end_date.strftime('%Y-%m-%d')
        calendar_suffix = '&max-results=30&alt=json'
        url = calendar_host + calendar_id + calendar_start + calendar_end + calendar_suffix
        log.debug("fetching holiday information from %s", url)
        raw_res = urllib2.urlopen(url)
        res = json.loads(raw_res.read())
        log.info("imported %d %s", len(res["feed"]["entry"]), " holidays")
        holidays = []
        for d in res["feed"]["entry"]:
            d_str = pattern.findall(d["id"]["$t"])[0]
            holidays.append(dt.datetime.strptime(d_str, '%Y%m%d').replace(tzinfo=pytz.timezone("Asia/Tokyo")))
        return holidays

    def register(self, working, start_date, end_date, holidays, human_mode_min=0):
        self.scheduler = Scheduler(timezone=pytz.timezone('Asia/Tokyo'), logger=log)
        today = dt.date.today()
        for w in working:
            # schedule shukkin
            h, m = map(int, w["from"].split(':'))
            fromtime = dt.time(h,m,tzinfo=pytz.timezone('Asia/Tokyo'))
            d = dt.datetime.combine(today, fromtime) - dt.timedelta(minutes=human_mode_min)
            trigger = CronTrigger(day_of_week=w["dayOfWeek"],
                                  hour=d.hour, minute=d.minute,
                                  start_date=start_date,
                                  end_date=end_date,
                                  timezone=pytz.timezone('Asia/Tokyo'))
            self.scheduler.add_job(self.worker.work_start,trigger)
            # schedule taikin
            h, m = map(int, w["till"].split(':'))
            tilltime = dt.time(h,m,tzinfo=pytz.timezone('Asia/Tokyo'))
            trigger = CronTrigger(day_of_week=w["dayOfWeek"],
                                  hour=tilltime.hour, minute=tilltime.minute,
                                  start_date=start_date,
                                  end_date=end_date,
                                  timezone=pytz.timezone('Asia/Tokyo'))
            self.scheduler.add_job(dispatch_after(human_mode_min,
                                                  self.worker.work_end),
                                   trigger)
        self.scheduler.print_jobs()

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()


if __name__ == '__main__':
    m = DakokuManager(config_path="config.json",
                      schedule_path="schedule.json")
    m.start()
