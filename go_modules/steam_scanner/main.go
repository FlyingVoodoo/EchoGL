package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	http.HandleFunc("/scan", scanHandler)

	port := ":8080"
	log.Printf("Go REST API server starting on port %s...\n", port)

	err := http.ListenAndServe(port, nil)
	if err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}

func scanHandler(w http.ResponseWriter, r *http.Request) {

	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	fmt.Fprintf(w, "Hello from Go REST API!")
}
