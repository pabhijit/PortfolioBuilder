# Use the Nginx image
FROM nginx

# Remove the default nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy our own configuration file
COPY nginx.conf /etc/nginx/conf.d/