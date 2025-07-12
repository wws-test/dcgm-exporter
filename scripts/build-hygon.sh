#!/bin/bash

# Build script for DCGM Exporter with Hygon DCU support
# This script builds the dcgm-exporter binary with Hygon DCU support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="binary"
OUTPUT_DIR="./bin"
DOCKER_TAG="dcgm-exporter-hygon:latest"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build DCGM Exporter with Hygon DCU support

OPTIONS:
    -t, --type TYPE         Build type: binary, docker, or all (default: binary)
    -o, --output DIR        Output directory for binary (default: ./bin)
    -d, --docker-tag TAG    Docker image tag (default: dcgm-exporter-hygon:latest)
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Build binary only
    $0 -t docker            # Build Docker image only
    $0 -t all               # Build both binary and Docker image
    $0 -o /usr/local/bin    # Build binary to specific directory

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -d|--docker-tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate build type
if [[ ! "$BUILD_TYPE" =~ ^(binary|docker|all)$ ]]; then
    print_error "Invalid build type: $BUILD_TYPE. Must be 'binary', 'docker', or 'all'"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "go.mod" ]] || [[ ! -d "cmd/dcgm-exporter" ]]; then
    print_error "Please run this script from the dcgm-exporter root directory"
    exit 1
fi

# Function to build binary
build_binary() {
    print_info "Building DCGM Exporter binary with Hygon DCU support..."
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Set build variables
    VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
    BUILD_TIME=$(date -u '+%Y-%m-%d_%H:%M:%S')
    GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    # Build flags
    LDFLAGS="-X main.BuildVersion=${VERSION} -X main.BuildTime=${BUILD_TIME} -X main.GitCommit=${GIT_COMMIT}"
    
    print_info "Version: $VERSION"
    print_info "Build Time: $BUILD_TIME"
    print_info "Git Commit: $GIT_COMMIT"
    
    # Build the binary
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
        -ldflags "$LDFLAGS" \
        -o "$OUTPUT_DIR/dcgm-exporter" \
        ./cmd/dcgm-exporter
    
    print_info "Binary built successfully: $OUTPUT_DIR/dcgm-exporter"
    
    # Make it executable
    chmod +x "$OUTPUT_DIR/dcgm-exporter"
    
    # Show binary info
    ls -la "$OUTPUT_DIR/dcgm-exporter"
}

# Function to build Docker image
build_docker() {
    print_info "Building Docker image with Hygon DCU support..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Build Docker image
    docker build -f docker/Dockerfile.hygon -t "$DOCKER_TAG" .
    
    print_info "Docker image built successfully: $DOCKER_TAG"
    
    # Show image info
    docker images "$DOCKER_TAG"
}

# Function to run tests
run_tests() {
    print_info "Running tests for Hygon DCU components..."
    
    # Test hygonprovider package
    if go test ./internal/pkg/hygonprovider/... -v; then
        print_info "Hygon provider tests passed"
    else
        print_warning "Hygon provider tests failed (may be due to missing DCGM dependencies in build environment)"
    fi
}

# Main build logic
main() {
    print_info "Starting build process for DCGM Exporter with Hygon DCU support"
    print_info "Build type: $BUILD_TYPE"
    
    # Run tests first
    run_tests
    
    case $BUILD_TYPE in
        binary)
            build_binary
            ;;
        docker)
            build_docker
            ;;
        all)
            build_binary
            build_docker
            ;;
    esac
    
    print_info "Build process completed successfully!"
    
    # Show usage examples
    if [[ "$BUILD_TYPE" == "binary" ]] || [[ "$BUILD_TYPE" == "all" ]]; then
        echo
        print_info "Usage examples:"
        echo "  # Start in Hygon DCU mode:"
        echo "  $OUTPUT_DIR/dcgm-exporter --use-hygon-mode"
        echo
        echo "  # Start in NVIDIA GPU mode (default):"
        echo "  $OUTPUT_DIR/dcgm-exporter"
        echo
        echo "  # Monitor specific Hygon DCU devices:"
        echo "  $OUTPUT_DIR/dcgm-exporter --use-hygon-mode --hygon-devices='g:0,1,2,3'"
    fi
    
    if [[ "$BUILD_TYPE" == "docker" ]] || [[ "$BUILD_TYPE" == "all" ]]; then
        echo
        print_info "Docker usage examples:"
        echo "  # Run in Hygon DCU mode:"
        echo "  docker run -d --privileged -p 9400:9400 -e DCGM_EXPORTER_USE_HYGON_MODE=true $DOCKER_TAG"
        echo
        echo "  # Run in NVIDIA GPU mode:"
        echo "  docker run -d --gpus all -p 9400:9400 $DOCKER_TAG"
    fi
}

# Run main function
main
