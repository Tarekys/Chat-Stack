FROM redis:7-alpine

# Use custom redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Set proper permissions
RUN chown redis:redis /usr/local/etc/redis/redis.conf

# Start redis with the custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
