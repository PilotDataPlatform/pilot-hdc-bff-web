set -e

DOCKER_REGISTRY="docker-registry.ebrains.eu"

TAG_MESSAGE="$1"
HDC_BRANCH="hdc"

# Check for --help argument to display usage information
if [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [--help] <tag message>"
    echo "This script automates the process of building and pushing the Docker image."
    echo "You'll need to make sure that the poetry version is patched (it will fail otherwise)."
    echo "You'll also need to pass the message to be used upon creation of the git tag:"
    echo ""
    echo "  ./build_and_push.sh \"Your commit message here\""
    echo ""
    echo "  # Example:"
    echo "  ./build_and_push.sh \"We fixed all the bugs in this latest change.\""
    echo ""
    exit 0
fi

TAG_MESSAGE="$1"

# make sure the git branch is $ENVIRONMENT and is up-to-date
git checkout $HDC_BRANCH
git pull origin $HDC_BRANCH

VERSION=$(poetry version -s)

# validate that portal version was passed as parameter
if [ -z "$VERSION" ]; then
    echo "Please provide the portal version to use."
    exit 1
fi 

# Exit with error if TAG_MESSAGE is empty
if [ -z "$TAG_MESSAGE" ]; then
    echo "Tag message must not be empty."
    exit 1
fi

# exit with error if there are conflicts
if [[ $(git ls-files -u) ]]; then
    echo "There are merge conflicts. Please resolve them before continuing."
    exit 1
fi

# Set necessary variables
DOCKER_TAG=$DOCKER_REGISTRY/hdc-services-image/bff-web:hdc-$VERSION

# Check if the Docker image with the given VERSION already exists in the registry
if docker manifest inspect $DOCKER_TAG >/dev/null; then
    echo "Docker image with version $VERSION already exists. Please update the poetry version."
    exit 1
fi

# Build and push docker image
docker build --tag $DOCKER_TAG --platform=linux/amd64 .

docker push $DOCKER_TAG

git tag -a $VERSION -m "$TAG_MESSAGE" 
git push origin $VERSION
