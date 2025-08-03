// go_modules/steam_scanner/main.go
package main

import (
	"encoding/json" // Для вывода JSON
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

// GameInfo represents the data we extract from an ACF file.
type GameInfo struct {
	AppID      string `json:"appid"`
	Name       string `json:"name"`
	InstallDir string `json:"installdir"`
	Path       string `json:"full_install_path"` // Full path to the game directory
	Source     string `json:"source"`            // e.g., "Steam"
}

// SteamLibrary represents a Steam library folder.
type SteamLibrary struct {
	Path string `json:"path"`
}

func main() {
	// This is just a placeholder for now.
	// We will implement the actual scanning logic here.
	// For testing purposes, let's return some dummy data.

	dummyGame := GameInfo{
		AppID:      "252490",
		Name:       "Rust (Dummy)",
		InstallDir: "Rust",
		Path:       "D:\\Steam test\\steamapps\\common\\Rust", // Replace with an actual path for your test
		Source:     "Steam",
	}

	dummyLibrary := SteamLibrary{
		Path: "D:\\Steam test\\steamapps", // Replace with an actual path for your test
	}

	// For now, just print some info. Later we'll output JSON.
	// fmt.Printf("Dummy Game: %+v\n", dummyGame)
	// fmt.Printf("Dummy Library: %+v\n", dummyLibrary)

	// Output as JSON for Python to consume
	output := struct {
		Games     []GameInfo     `json:"games"`
		Libraries []SteamLibrary `json:"libraries"`
	}{
		Games:     []GameInfo{dummyGame},
		Libraries: []SteamLibrary{dummyLibrary},
	}

	jsonOutput, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(jsonOutput))
}

// parseVDF tries to parse a VDF file, looking for "key" "value" pairs.
func parseVDF(content string, key string) (string, error) {
	// Regular expression to find "key" "value" pairs
	rePattern := fmt.Sprintf(`"%s"\s+"([^"]+)"`, regexp.QuoteMeta(key))
	re := regexp.MustCompile(rePattern)
	match := re.FindStringSubmatch(content)
	if len(match) > 1 {
		return match[1], nil
	}
	return "", fmt.Errorf("key %s not found", key)
}

// Placeholder for actual Windows registry parsing (requires external module or CGO)
// We'll focus on file parsing first.
func findSteamPathFromRegistryWindows() (string, error) {
	// This part is tricky in pure Go without external libraries.
	// For simplicity, we might hardcode common paths or rely on user input initially
	// or use a CGO solution. Let's start with common paths for cross-platform.
	return "", fmt.Errorf("Windows registry parsing not implemented in pure Go")
}

// findPotentialSteamAppsFolders is the main function to find all steamapps folders.
func findPotentialSteamAppsFolders() ([]string, error) {
	var steamAppsPaths []string

	// Common paths for Windows (need to be adjusted for Go's path handling)
	commonWinPaths := []string{
		`C:\Program Files (x86)\Steam`,
		`C:\Program Files\Steam`,
	}
	for _, drive := range "CDEFGHIJKLMNOPQRSTUVWXYZ" {
		commonWinPaths = append(commonWinPaths, fmt.Sprintf("%c:\\Steam", drive))
		commonWinPaths = append(commonWinPaths, fmt.Sprintf("%c:\\SteamLibrary", drive))
		commonWinPaths = append(commonWinPaths, fmt.Sprintf("%c:\\Games\\Steam", drive))
		commonWinPaths = append(commonWinPaths, fmt.Sprintf("%c:\\Games", drive))
	}

	// Common paths for Linux
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get home directory: %v", err)
	}
	commonLinuxPaths := []string{
		filepath.Join(homeDir, ".steam", "steam"),
		filepath.Join(homeDir, ".local", "share", "Steam"),
		"/opt/steam",
		"/usr/share/steam",
		"/mnt",
		"/media",
	}

	// Common paths for macOS
	commonMacOSPaths := []string{
		"/Applications/Steam.app/Contents/SteamOS",
		filepath.Join(homeDir, "Library", "Application Support", "Steam"),
	}

	// Combine paths based on OS
	var scanPaths []string
	switch os := runtime.GOOS; os {
	case "windows":
		scanPaths = commonWinPaths
		// Attempt to read from registry (if implemented or using external tool)
		// steamPath, err := findSteamPathFromRegistryWindows()
		// if err == nil && steamPath != "" {
		// 	scanPaths = append(scanPaths, steamPath)
		// }
	case "linux":
		scanPaths = commonLinuxPaths
	case "darwin":
		scanPaths = commonMacOSPaths
	default:
		return nil, fmt.Errorf("unsupported operating system: %s", os)
	}

	checkedMainFolders := make(map[string]bool)

	for _, p := range scanPaths {
		path := filepath.Clean(p)
		info, err := os.Stat(path)
		if err != nil || !info.IsDir() {
			continue
		}

		// If it's directly a "steamapps" folder
		if strings.ToLower(filepath.Base(path)) == "steamapps" {
			steamAppsPaths = append(steamAppsPaths, path)
			checkedMainFolders[filepath.Dir(path)] = true // Mark parent as checked
		} else if info, err = os.Stat(filepath.Join(path, "steamapps")); err == nil && info.IsDir() {
			steamAppsPath := filepath.Join(path, "steamapps")
			steamAppsPaths = append(steamAppsPaths, steamAppsPath)
			checkedMainFolders[path] = true // Mark this as a main Steam folder
		} else if strings.ToLower(filepath.Base(path)) == "steamlibrary" {
			// Check for SteamLibrary/steamapps
			steamAppsInLibPath := filepath.Join(path, "steamapps")
			if info, err = os.Stat(steamAppsInLibPath); err == nil && info.IsDir() {
				steamAppsPaths = append(steamAppsPaths, steamAppsInLibPath)
				checkedMainFolders[path] = true // Mark this as a main SteamLibrary folder
			}
		}
	}

	// Parse libraryfolders.vdf from known main Steam folders
	for mainFolder := range checkedMainFolders {
		libraryVDFPath := filepath.Join(mainFolder, "steamapps", "libraryfolders.vdf")
		if info, err := os.Stat(libraryVDFPath); err == nil && !info.IsDir() {
			content, err := os.ReadFile(libraryVDFPath)
			if err != nil {
				// fmt.Fprintf(os.Stderr, "Error reading %s: %v\n", libraryVDFPath, err)
				continue
			}

			// Use regex to find all "path" values
			re := regexp.MustCompile(`"\d+"\s+"([^"]+)"`)
			matches := re.FindAllStringSubmatch(string(content), -1)
			for _, match := range matches {
				if len(match) > 1 {
					libPath := strings.ReplaceAll(match[1], "\\\\", string(os.PathSeparator))
					steamAppsPath := filepath.Join(libPath, "steamapps")
					if info, err = os.Stat(steamAppsPath); err == nil && info.IsDir() {
						steamAppsPaths = append(steamAppsPaths, steamAppsPath)
					}
				}
			}
		}
	}

	// Deduplicate paths
	uniquePaths := make(map[string]bool)
	var result []string
	for _, path := range steamAppsPaths {
		if !uniquePaths[path] {
			uniquePaths[path] = true
			result = append(result, path)
		}
	}

	return result, nil
}

// scanSteamAppsFolder scans a given steamapps folder for ACF files.
func scanSteamAppsFolder(steamAppsPath string) ([]GameInfo, error) {
	var games []GameInfo
	acfPattern := filepath.Join(steamAppsPath, "appmanifest_*.acf")
	matches, err := filepath.Glob(acfPattern)
	if err != nil {
		return nil, fmt.Errorf("error globbing ACF files in %s: %v", steamAppsPath, err)
	}

	for _, acfPath := range matches {
		content, err := os.ReadFile(acfPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error reading ACF file %s: %v\n", acfPath, err)
			continue
		}

		// Parse AppID, Name, InstallDir
		appid, _ := parseVDF(string(content), "appid")
		name, _ := parseVDF(string(content), "name")
		installdir, _ := parseVDF(string(content), "installdir")

		if appid != "" && name != "" && installdir != "" {
			commonPath := filepath.Join(steamAppsPath, "common")
			fullInstallPath := filepath.Join(commonPath, installdir)

			// Check if the directory actually exists
			if info, err := os.Stat(fullInstallPath); err == nil && info.IsDir() {
				games = append(games, GameInfo{
					AppID:      appid,
					Name:       name,
					InstallDir: installdir,
					Path:       fullInstallPath,
					Source:     "Steam",
				})
			} else {
				// fmt.Fprintf(os.Stderr, "Warning: Game install directory not found at %s for AppID %s\n", fullInstallPath, appid)
				games = append(games, GameInfo{
					AppID:      appid,
					Name:       name,
					InstallDir: installdir,
					Path:       "N/A - Not Found",
					Source:     "Steam",
				})
			}
		}
	}
	return games, nil
}
