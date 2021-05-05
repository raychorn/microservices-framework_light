import datetime

import calendar

def get_next_monday(year, month, day):
    date0 = datetime.date(year, month, day)
    next_monday = date0 + datetime.timedelta(7 - date0.weekday() or 7)
    return next_monday

today = datetime.date.today()
print(get_next_monday(today.year, today.month, today.day))

cal = calendar.Calendar(firstweekday=0)
for dt in cal.itermonthdays2(today.year, today.month):
    print(dt)
