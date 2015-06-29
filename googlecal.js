var request = require('request');
var inspect = require('util').inspect;
var _ = require('lodash');
var log4js = require('log4js');
log4js.configure('./log-config.json');
var log = log4js.getLogger('access');

var parseUrlToDate = function(url){
  var pattern = new RegExp(/^.*basic\/([0-9]*)_.*$/);
  var res = url.match(pattern);
  log.debug("lstrip: " + res[1]);
  return res[1];
}

exports.GetHolidays = function(start, end, cb){
  var calendar_id = 'japanese__ja@holiday.calendar.google.com';
  var req_option = {
    url: 'https://www.google.com/calendar/feeds/' + calendar_id + '/public/basic?start-min=' + start + '&start-max=' + end + '&max-results=30&alt=json',
    json: true
  };

  log.info('fetching holiday information from google calendar: ' + req_option.url);
  request(req_option, function(err, res, body){
    if(!err && res.statusCode === 200) {
      log.info('found ' + body.feed.entry.length + ' holidays');
      cb(_.map(body.feed.entry, function(e){
        return parseUrlToDate(e.id.$t);
      }));
    } else {
      var err_msg = '' + err + body;
      log.error('failed to fetch holiday information: ' + err_msg);
      cb(null);
    }
  });
};
