from flask import render_template, redirect, request, url_for
from pymongo.errors import ServerSelectionTimeoutError

def queries_mongodb(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServerSelectionTimeoutError as e:
            print(e)
            return render_template('mongo_error.html'), 503
    
    # Bad practice, but this is what flask uses in the background
    wrapper.__name__ = func.__name__
    return wrapper

def redirect_dest(fallback):
    dest = request.args.get('next')
    return redirect(dest or fallback)
