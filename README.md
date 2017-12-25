# ColorShift
I hate images that look good, so I wrote a program that fixes them. 
After 'fixing', images will contain no identically colored pixels (with some exceptions).

Semi-legalish note:
I made this. Talk to me before stealing it (email TimJEwing@gmail.com, or message me on reddit /u/redhotchilirocket), but using it for personal stuff is cool.

Other notes:
 - Run it with 'python Colorator.py (FILENAME) (APPROPRIATE COLORSIZE)', or just 'python Colorator.py -h'
 - It makes every pixel unique, except when:
   - You use HSV. HSV sucks, since (0, 0, 0) and (255, 0, 0) are both black.
   - Your colorsize is wrong. Not really sure what happens here, since it seems to change every time I update the code and I'll prolly never update the readme again
   - Other bad things happen. Really I've only checked that it works with some of the options cause this is just a side project and I don't care.
