build:
	docker build . --tag hieu-map
run:
	docker run hieu-map -v "${pwd}"/target:/app
run2:
	docker run --name devtest --mount source=myvol,target=/app hieumap
dev:
	docker run -it $(docker build . --tag hieumap)