var request = require('request');
var async = require('async');
var _ = require('lodash');
var inspect = require('util').inspect;
var Nightmare = require('nightmare');
var config = require('./config');
var schedule = require('./schedule');
var moment = require('moment');

var log4js = require('log4js');
log4js.configure('./log-config.json');
var log = log4js.getLogger('access');

var node_sched = require('node-schedule');

var Login = function(){
  return Nightmare()
    .goto(config.host)
    .wait()
    .url(function(url){
      log.info('access to: ' + url);
    })
    .type('input[name="user_id"]', config.user)
    .type('input[name="password"]', config.pass);
};

var doShukkin = function(){
  return Login()
    .click('input[name="syussya"]')
    .wait();
};

var doTaikin = function(){
  return Login()
    .click('input[name="taisya"]')
    .wait();
};

var checkIfHolidays = function(holidays, func) {
  var now = moment();
  if(!_.every(holidays, now.format('YYYYMMDD'))){
    func();
  } else {
    log.info('skipping on ' + now.format('YYYY-MM-DD'));
  }
};

var random = function(max) {
  return Math.random() * max;
}

var shukkin = function(holidays) {
  checkIfHolidays(holidays, function() {
    setTimeout(doShukkin, random(config.human_mode));
  });
};

var taikin = function(holidays) {
  checkIfHolidays(holidays, function() {
    setTimeout(doTaikin, random(config.human_mode * 60));
  });
};


var setSchedule = function(holidays){
  var jobs = [];
  for (var i = 0; i < schedule.working.length; i++){
    var worktime = schedule.working[i];
    var fromtime = moment()
      .day(i+1)
      .hour(worktime.from.split(':')[0])
      .minute(worktime.from.split(':')[1])
      .add(-1 * config.human_mode, 'minutes');
    var tilltime = moment()
      .day(i+1)
      .hour(worktime.till.split(':')[0])
      .minute(worktime.till.split(':')[1]);
    console.log('register from: ' + worktime.from);
    var rule_from = new node_sched.RecurrenceRule();
    rule_from.dayOfWeek = fromtime.day();
    rule_from.hour = fromtime.hour();
    rule_from.minute = fromtime.minute();
    jobs.push(node_sched.scheduleJob(rule_from, function(){ shukkin(holidays); }));
    console.log('register till: ' + worktime.till);
    var rule_till = new node_sched.RecurrenceRule();
    rule_till.dayOfWeek = tilltime.day();
    rule_till.hour = tilltime.hour();
    rule_till.minute = tilltime.minute();
    jobs.push(node_sched.scheduleJob(rule_till, function(){ taikin(holidays); }));
  }
  return jobs;
};

var gcal = require('./googlecal');
gcal.GetHolidays(schedule.valid.start, schedule.valid.end, function(holidays){
  var jobs = setSchedule(holidays);
  _.map(jobs, function(j){
    console.log(inspect(j));
  });
});
