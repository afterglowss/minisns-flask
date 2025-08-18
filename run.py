from app import create_app
app = create_app()
print(app.url_map)
if __name__ == "__main__":
    app.run(debug=True)
# This file is the entry point for running the Flask application.
# It imports the create_app function from the app package and runs the application with debug mode enabled.
# This allows for easier development and debugging of the Flask application.