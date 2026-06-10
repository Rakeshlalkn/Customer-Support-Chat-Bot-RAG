# Frontend image — static files served by nginx
FROM nginx:1.27-alpine

# Replace the default nginx config with one that proxies /api -> backend
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
