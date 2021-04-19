is_really_something = lambda s,t:(s is not None) and (((not callable(t)) and isinstance(s, t)) or ((callable(t) and t(s))))
is_really_something_with_stuff = lambda s,t:is_really_something(s,t) and (len(s) > 0)
something_greater_than_zero = lambda s:(s > 0)
default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]
