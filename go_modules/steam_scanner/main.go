package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

type GameInfo struct {
	AppID      string `json:"appid"`
	Name       string `json:"name"`
	InstallDir string `json:"installdir"`
	Path       string `json:"full_install_path"`
	Source     string `json:"source"`
}

type SteamLibrary struct {
	Path string `json:"path"`
}

func main() {

	dummyGame := GameInfo{
		AppID:      "252490",
		Name:       "Rust (Dummy)",
		InstallDir: "Rust",
		Path:       "D:\\Steam test\\steamapps\\common\\Rust",
		Source:     "Steam",
	}

	dummyLibrary := SteamLibrary{
		Path: "D:\\Steam test\\steamapps",
	}

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

func parseVDF(content string, key string) (string, error) {
	rePattern := fmt.Sprintf(`"%s"\s+"([^"]+)"`, regexp.QuoteMeta(key))
	re := regexp.MustCompile(rePattern)
	match := re.FindStringSubmatch(content)
	if len(match) > 1 {
		return match[1], nil
	}
	return "", fmt.Errorf("key %s not found", key)
}

func findSteamPathFromRegistryWindows() (string, error) {

	return "", fmt.Errorf("Windows registry parsing not implemented in pure Go")
}

func findPotentialSteamAppsFolders() ([]string, error) {
	var steamAppsPaths []string

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

	commonMacOSPaths := []string{
		"/Applications/Steam.app/Contents/SteamOS",
		filepath.Join(homeDir, "Library", "Application Support", "Steam"),
	}

	var scanPaths []string
	switch os := runtime.GOOS; os {
	case "windows":
		scanPaths = commonWinPaths
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

		if strings.ToLower(filepath.Base(path)) == "steamapps" {
			steamAppsPaths = append(steamAppsPaths, path)
			checkedMainFolders[filepath.Dir(path)] = true
		} else if info, err = os.Stat(filepath.Join(path, "steamapps")); err == nil && info.IsDir() {
			steamAppsPath := filepath.Join(path, "steamapps")
			steamAppsPaths = append(steamAppsPaths, steamAppsPath)
			checkedMainFolders[path] = true
		} else if strings.ToLower(filepath.Base(path)) == "steamlibrary" {
			steamAppsInLibPath := filepath.Join(path, "steamapps")
			if info, err = os.Stat(steamAppsInLibPath); err == nil && info.IsDir() {
				steamAppsPaths = append(steamAppsPaths, steamAppsInLibPath)
				checkedMainFolders[path] = true
			}
		}
	}

	for mainFolder := range checkedMainFolders {
		libraryVDFPath := filepath.Join(mainFolder, "steamapps", "libraryfolders.vdf")
		if info, err := os.Stat(libraryVDFPath); err == nil && !info.IsDir() {
			content, err := os.ReadFile(libraryVDFPath)
			if err != nil {
				continue
			}

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

		appid, _ := parseVDF(string(content), "appid")
		name, _ := parseVDF(string(content), "name")
		installdir, _ := parseVDF(string(content), "installdir")

		if appid != "" && name != "" && installdir != "" {
			commonPath := filepath.Join(steamAppsPath, "common")
			fullInstallPath := filepath.Join(commonPath, installdir)

			if info, err := os.Stat(fullInstallPath); err == nil && info.IsDir() {
				games = append(games, GameInfo{
					AppID:      appid,
					Name:       name,
					InstallDir: installdir,
					Path:       fullInstallPath,
					Source:     "Steam",
				})
			} else {
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
