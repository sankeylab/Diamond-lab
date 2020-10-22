h0, b0 = histogram(d[0], bins=50)
h1, b1 = histogram(d[1], bins=50)
h2, b2 = histogram(d[2], bins=50)


x = ( b0[1:], b1[1:], b2[1:])
y = ( h0, h1, h2)

xlabels = 'counts'
ylabels = ( 'c0' , 'c1', 'c2')
