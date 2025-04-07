# Use an official Node runtime as a parent image
FROM node:18-alpine as build

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./
# If using yarn, uncomment the next line and comment out the npm ci line
# COPY yarn.lock ./

# Install dependencies
# Use ci for faster, reproducible installs
RUN npm ci
# If using yarn, uncomment the next line and comment out the npm ci line
# RUN yarn install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Build the React app for production
# Use the build script defined in package.json
RUN npm run build
# If using yarn, uncomment the next line and comment out the npm run build line
# RUN yarn build

# Stage 2: Serve the static files using Nginx
FROM nginx:1.21-alpine

# Copy the build output from the build stage to Nginx html directory
COPY --from=build /app/build /usr/share/nginx/html

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy the entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Set the entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start Nginx when the container launches (this will be passed to the entrypoint)
CMD ["nginx", "-g", "daemon off;"]