import logging 
from flask import Flask,render_template, request
from google.cloud import storage
import pymysql
import time
from datetime import datetime

app=Flask(__name__)

gcs = storage.Client.from_service_account_json("/home/shilpashreesvp/cloud_7/static/shilpa_shree.json")

# Get the bucket that the file will be uploaded to.
bucket = gcs.get_bucket('')

host = ""
dbname = ""
user = ""
password = ""
cloud_unix_socket=''

conn = pymysql.connect( host=host,user=user, passwd=password, db=dbname)
conn.autocommit(True)
print "Database connected"
cur=conn.cursor()

img_links = "https://storage.googleapis.com/shilpa-bucket/"

@app.route('/')
def hello_world():
	return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_user():
	username_be=request.form['username']
	password_be=request.form['password']
	print (username_be)
	print (password_be)
	query="select * from admin where username='"+username_be+"' and password='"+password_be+"'"
    	cur.execute(query)
	row_count = cur.rowcount
	print (row_count)
	if row_count==0:
		return "Invalid Credentials"
	else:
		return render_template("index.html",username=username_be)

@app.route('/upload', methods=['POST'])
def upload():
	username=request.form['username']
	f = request.files.get('file')
    	title = request.form['title']
    	ratings = request.form['ratings']
    	comments = request.form['comments']
    	print(f.filename)

    	# Create a new blob and upload the file's content.
    	blob = bucket.blob(f.filename)

    	blob.upload_from_string(
        	f.read(),
        	content_type=f.content_type
    	)
    	blob.make_public()

    	image_url = img_links + f.filename

    	print(image_url)

    	query = """insert into picture_table (username,image_url,filename,title, comments, ratings,time) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    	cur.execute(query,(username,image_url,f.filename,title,comments,ratings,datetime.now()))
    	conn.commit()
    	return "upload successful"


@app.route('/view', methods=['POST'])
def view():
    	if request.method == 'POST':
		if request.form['click'] == 'View Image':
            		cur.execute("""SELECT * FROM picture_table""")
            		data = (cur.fetchall())
			instagram = [dict(image_url=row['image_url'],
                	        	title=row['title'],
                        		comments=row['comments'],
                              		ratings=row['ratings'],
                              		date_time=row['time']) for row in data]

            		print(instagram)

            	# return '<img src="' + image_links[0]+ '"/>'
	return render_template("gallery.html", instagram=instagram)


@app.route('/search', methods=['POST'])
def search():
    query="select creator from descriptions"
    print(query)
    cur.execute(query)
    data = cur.fetchall()
    print(data)
    creator_name = [dict(creator=row[0]) for row in data]
	
    return render_template("search.html",creator_name=creator_name)
	
@app.route('/createDB', methods=['POST'])
def createDB():
    	tablename = request.form['table_name']

    	file_name = tablename+'.csv'
    	f_obj = open(file_name, 'r')
    	reader = csv.reader(f_obj)

    	headers = next(reader, None)
    	print(headers)


    	if request.form['click'] == 'Create Table':
    # Table Create
        	create_query = 'Create table IF NOT EXISTS ' + dbname + '.' + tablename + ' ( '
        	for heading in headers:
            		create_query += heading + " varchar(1000) DEFAULT NULL,"

	        create_query = create_query[:-1]
        	create_query += ")"
        	print(create_query)
        	cur.execute(create_query)
        	print('Table Created')

        	print(file_name)
        	print("loding insert query")
        	# Load Data via CSV File
        	insert_query = """LOAD DATA LOCAL INFILE '""" +file_name+ """' INTO TABLE """+tablename+""" FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'LINES TERMINATED BY '\n' IGNORE 1 LINES"""
        	print("insert query executed")
        	cur.execute(insert_query)
        	conn.commit()

        return 'Table Created with Uploaded Schema'

@app.route('/search_image', methods=['POST'])
def search_image():

    user_i_time = time.time()

    search_string = request.form['search']

    query = """select filename,title, creator from descriptions where Description like'%"""+search_string+"""%'"""
    cloud_i_time = time.time()
    cur.execute(query)
    data1 = cur.fetchall()
    
    instagram = [dict(image_url="https://storage.googleapis.com/shilpa-bucket/"+row[0],
                      title=row[1],
                      creator=row[2]) for row in data1]
    print(instagram)
    user_f_time = time.time()
    cloud_f_time = time.time()
    user_time = user_f_time - user_i_time
    cloud_time = cloud_f_time - cloud_i_time

    return render_template("gallery.html", instagram=instagram,user_time=user_time, cloud_time = cloud_time,description=search_string)

@app.route('/search_image_creator', methods=['POST'])
def search_image_creator():
	user_i_time = time.time()
	search_string = request.form['creator']

    	query = """select filename,title, creator from descriptions where creator ='"""+search_string+"""'"""
    	cloud_i_time = time.time()
    	cur.execute(query)
    	data1 = cur.fetchall()
    
    	instagram = [dict(image_url="https://storage.googleapis.com/shilpa-bucket/"+row[0],
        	              title=row[1],
        	              creator=row[2]) for row in data1]

    	print(instagram)
    	user_f_time = time.time()
    	cloud_f_time = time.time()
    	user_time = user_f_time - user_i_time
    	cloud_time = cloud_f_time - cloud_i_time

    	return render_template("gallery.html", instagram=instagram,user_time=user_time, cloud_time = cloud_time)

@app.route('/delete', methods=['POST'])
def delete():	
	user_i_time = time.time()
	delete_string=request.form['files']
	get_creator="""select creator from descriptions where Title='"""+delete_string+"""'"""
	cur.execute(get_creator)
	creator=cur.fetchone()
	query="""delete from descriptions where Title='"""+delete_string+"""'"""	
    	cur.execute(query)
    	conn.commit()
    	cloud_i_time = time.time()
    	
    	query2 = """select filename,title, creator from descriptions where creator ='"""+creator[0]+"""'"""
    	print(query2)
    	cur.execute(query2)
    	data1 = cur.fetchall()
    	print(data1)
    	instagram = [dict(image_url="https://storage.googleapis.com/shilpa-bucket/"+row[0],
        		              title=row[1],
        		              creator=row[2]) for row in data1]

    	print(instagram)
    	user_f_time = time.time()
    	cloud_f_time = time.time()
    	user_time = user_f_time - user_i_time
    	cloud_time = cloud_f_time - cloud_i_time

    	return render_template("gallery.html", instagram=instagram,user_time=user_time, cloud_time = cloud_time)

@app.route('/rename', methods=['POST'])
def rename():
	user_i_time = time.time()
	image_url=request.form['image_url']
	name_string=request.form['name_change']
	title=request.form['file_source']	
	descrip=request.form['description']
	print(descrip)
	get_creator="""select filename from descriptions where Title='"""+title+"""'"""
	cur.execute(get_creator)
	oldfilename=cur.fetchone()
	old=oldfilename[0]
	print(old)
	blob = bucket.blob(old)
	print(blob)
	print(name_string)
	bucket.rename_blob(old,name_string)
	
	query="""update descriptions set filename='"""+name_string+"""' where title='"""+title+"""'"""
    	cur.execute(query)
    	conn.commit()
    	cloud_i_time = time.time()
    	
    	query2 = """select filename,title, creator from descriptions where description like '%"""+descrip+"""%'"""
    	print(query2)
    	cur.execute(query2)
    	data1 = cur.fetchall()
    	print(data1)
    	instagram = [dict(image_url="https://storage.googleapis.com/shilpa-bucket/"+row[0],
        		              title=row[1],
        		              creator=row[2]) for row in data1]

    	print(instagram)
    	user_f_time = time.time()
    	cloud_f_time = time.time()
    	user_time = user_f_time - user_i_time
    	cloud_time = cloud_f_time - cloud_i_time

    	return render_template("gallery.html", instagram=instagram,user_time=user_time, cloud_time = cloud_time)
		
    	
if __name__ == '__main__':
    app.run(debug="True")
