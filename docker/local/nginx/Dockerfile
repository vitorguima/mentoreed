FROM nginx:1.23.3-alpine

# Need to remove the default.conf file that comes with the nginx image and then add the new one
RUN rm /etc/nginx/conf.d/default.conf

COPY ./default.conf /etc/nginx/conf.d/default.conf