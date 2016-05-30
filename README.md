# NHS-Tutoring, by Christopher Grossack, 2014

A flask website meant for handling tutor assignments for National Honors Society.

Originally developed for use at Simsbury High School, CT.

---

NOTE: This was made by my highschool self in 2014. I didn't know what automated testing was back then.<br> 
I'm posting this so that people can use it, but I only really made sure the program ran at all.<br>
That said, I didn't go through the code at all, but I did go through this README and the instructions in config.py to make sure they aren't EXTREMELY snarky.

Long story short, I may or may not start working on this again, but if you find anything that doesn't work, please email me and it will probably be a simple fix.

---

##FEATURES:

###Varied period structure:

Different number of periods every day? works great<br>
Have school saturday, not wednesday? got you covered

###Varied subject structure:

Need a really math heavy curriculum? you can do that<br>
Need to get rid of the history classes entirely? that's a thing<br>
Want to add an engineering curriculum? also easy.

###Email reminders:
Tutors and students will be emailed on the day of their meeting regarding the other party, the subject, and the period<br>
Administrators can send a mass email, filtered by which subjects a given person can tutor, from the admin menu

###Master Schedule:
The Administrators can view the weeks tutoring assignments in a convenient layout.<br>
Additionally, every time the master schedule page is accessed, a CSV file containing the same information is updated for external recordkeeping.<br>

###Tutoring Assignment:
Tutors and students can select any periods during which they are free.<br>
Tutors can select any subjects in which they feel confident tutoring others.<br>
When a student requests a tutor, the tutors presented are those currently tutoring the fewest others. This prevents Aaron Aaronson from ending up tutoring everybody, and spreads the workload more equally.<br>
If no tutors are available, the student is presented with an administrator's email address to try to find somebody willing to tutor.

###Banners:
Want to change the favicon or banner in the top left? go for it. /app/static/images

---

##HOW TO USE:

Flask Website Hosting would be a good google search for much more in depth explanations than I can give you here.

That said, I can tell you what everything does, and how to run a basic setup with ngrok.

###step 0 - right click edit config.py and read the instructions thoroughly.<br>
  step 0a: no seriously, read the instructions.<br>
  step 0b: now change things to suit your school system based on the instructions.<br>

###step 1 - Use pip and requirements.txt to set up a python environment and run the conveniently named run.py

  step 1a: open terminal or cmd and run "pip install -r requirements.txt" without the quotes to get the dependencies for NHS tutoring.
  step 1b: go to your webbrowser of choice, type localhost:5000 into the address bar. You should be greeted with the NHS tutoring homepage.
  
  NOTE: As of now, you can only see this website on YOUR computer. We'll fix this (albeit unsafely) in the next step.

###step 2 - set up a tunnel to your localhost with ngrok.

  This is insecure. It works, but it's not the best way of doing things.<br>
  For a more robust approach, I point you yet again towards googling Flask Website Hosting

  step 2a: download ngrok
  step 2b: open terminal or cmd in the root of the ngrok folder you downloaded
  step 2c: type "ngrok 5000" without quotes into your terminal/cmd
  step 2d: webbrowse to the disgusting website.ngrok.com you'll be presented with
  step 2e: you should again be greeted with the NHS tutoring homepage, but now you can access it with that disgusting link from anywhere.

###step 3 - set up some sort of timer service to run check_date.py every morning

  Depending on your systems, there are a variety of ways to do this. However, it IS important that this script be run every day.<br>
  If you're unsure how to do this:<br>

    For linux, google cronjob linux.
    For mac, google cronjob mac.
    For windows, google scheduled tasks.

###step 4 (optional) - contact me a HallaSurvivor@gmail.com for any obscure problems you're encountering.
  note: if you don't change the default email, emailing won't work.<br>
  note2: You should seriously read the instructions in config.py, and change anything you need to.
  note3: I am always here to help :)

---

#==Thank You Section==

I would like to give a huge thanks to everybody who helped make this site possible, starting with Matt Nardoza, who was the highschool friend who got me interested in making this site in the first place. Further, I would like to thank Miguel at http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database. Thanks to Miguel for both the scripts as well as a decent percentage of the knowledge that went into creating this website. I would similarly like to thank Real Python at https://realpython.com/blog/python/python-web-applications-with-flask-part-i/ for lots of knowledge, as well as the basis for my own mixin regarding commiting data, and Lalith Polepeddi at http://code.tutsplus.com/tutorials/intro-to-flask-signing-in-and-out--net-29982 for helping me through a variety of problems with my first database (users) and explaining it to me like I'm 5 with pictures and simple text. Thanks as well to Michael Lee, who had attempted to make a Flask-based NHS website before me, and who I emailed in an act of despair. He took the time to send mea wonderfully in depth email explaining everything he had done, so that I could start as far from total nothingness as possible. The website owes a huge part of its existence to him. Finally, a huge thank you to the stackexchange community, particularly stackoverflow. The questions of those who came before me and the helpful, insightful, and simultaneously in depth and easily understandable answers helped me through every problem I came across. Obviously the docs, official tutorials, and hours of reading other peoples blogs and tutorials that were lost in my history were indisposable, and I thank everybody else who I am unable to thank personally.
