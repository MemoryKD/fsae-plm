/**
 * PlmBridge.cpp - HTTP communication with FSAE-PLM backend
 *
 * Uses Windows WinHTTP API for HTTP requests.
 * nlohmann/json for JSON parsing (header-only library).
 * JWT token stored in Windows registry under HKCU\SOFTWARE\FSAE_PLM.
 */
#include "PlmBridge.h"

// Windows HTTP API
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")

// Registry
#include <winreg.h>

// nlohmann/json (header-only, place json.hpp in resources/)
// #include "nlohmann/json.hpp"
// using json = nlohmann::json;

#include <cstring>
#include <cstdio>

static const char* REGISTRY_PATH = "SOFTWARE\\FSAE_PLM";

PlmBridge::PlmBridge()
    : _loggedIn(false)
{
    memset(_serverUrl, 0, sizeof(_serverUrl));
    memset(_token, 0, sizeof(_token));
    memset(_lastError, 0, sizeof(_lastError));
    strcpy_s(_serverUrl, "http://localhost/api");
    LoadConfig();
}

PlmBridge::~PlmBridge()
{
    SaveConfig();
}

void PlmBridge::SetServerUrl(const char* url)
{
    strncpy_s(_serverUrl, url, sizeof(_serverUrl) - 1);
}

const char* PlmBridge::GetServerUrl() const { return _serverUrl; }
bool PlmBridge::IsLoggedIn() const { return _loggedIn; }
const char* PlmBridge::GetLastError() const { return _lastError; }

void PlmBridge::SetError(const char* error)
{
    strncpy_s(_lastError, error, sizeof(_lastError) - 1);
}

bool PlmBridge::Login(const char* username, const char* password)
{
    // Build JSON request body
    char body[512];
    sprintf_s(body, "{\"username\":\"%s\",\"password\":\"%s\"}", username, password);

    char response[4096];
    if (!HttpPost("auth/login", body, response, sizeof(response)))
    {
        SetError("HTTP request failed");
        return false;
    }

    // Parse response to extract access_token
    // TODO: Use nlohmann/json to parse
    // json j = json::parse(response);
    // strncpy_s(_token, j["access_token"].get<std::string>().c_str(), sizeof(_token) - 1);

    // Temporary: manual JSON parsing for access_token
    const char* tokenStart = strstr(response, "\"access_token\":\"");
    if (tokenStart)
    {
        tokenStart += 16; // skip the key
        const char* tokenEnd = strchr(tokenStart, '"');
        if (tokenEnd)
        {
            int len = (int)(tokenEnd - tokenStart);
            if (len < (int)sizeof(_token))
            {
                strncpy_s(_token, tokenStart, len);
                _loggedIn = true;
                SaveConfig();
                return true;
            }
        }
    }

    SetError("Failed to parse login response");
    return false;
}

void PlmBridge::Logout()
{
    memset(_token, 0, sizeof(_token));
    _loggedIn = false;
    SaveConfig();
}

bool PlmBridge::HttpGet(const char* path, char* response, int responseSize)
{
    // Parse server URL to get host and port
    char host[256] = {};
    int port = 80;
    bool useHttps = false;

    // Simple URL parsing: http://host:port/path
    const char* p = _serverUrl;
    if (strncmp(p, "https://", 8) == 0) { useHttps = true; p += 8; port = 443; }
    else if (strncmp(p, "http://", 7) == 0) { p += 7; }

    const char* colon = strchr(p, ':');
    const char* slash = strchr(p, '/');
    if (colon && (!slash || colon < slash))
    {
        strncpy_s(host, p, (int)(colon - p));
        port = atoi(colon + 1);
    }
    else if (slash)
    {
        strncpy_s(host, p, (int)(slash - p));
    }
    else
    {
        strcpy_s(host, p);
    }

    // Convert host to wide string for WinHTTP
    wchar_t whost[256];
    MultiByteToWideChar(CP_UTF8, 0, host, -1, whost, 256);

    // Build full path with API prefix
    char fullPath[512];
    sprintf_s(fullPath, "/api/%s", path);
    wchar_t wpath[512];
    MultiByteToWideChar(CP_UTF8, 0, fullPath, -1, wpath, 512);

    HINTERNET hSession = WinHttpOpen(L"FSAE-PLM CAA Client",
                                      WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                      WINHTTP_NO_PROXY_NAME,
                                      WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) { SetError("WinHttpOpen failed"); return false; }

    HINTERNET hConnect = WinHttpConnect(hSession, whost, (INTERNET_PORT)port, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); SetError("WinHttpConnect failed"); return false; }

    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", wpath,
                                             NULL, WINHTTP_NO_REFERER,
                                             WINHTTP_DEFAULT_ACCEPT_TYPES,
                                             useHttps ? WINHTTP_FLAG_SECURE : 0);
    if (!hRequest)
    {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        SetError("WinHttpOpenRequest failed");
        return false;
    }

    // Add Authorization header if logged in
    if (_token[0])
    {
        wchar_t authHeader[2100];
        swprintf_s(authHeader, L"Authorization: Bearer %S", _token);
        WinHttpAddRequestHeaders(hRequest, authHeader, (DWORD)-1L, WINHTTP_ADDREQ_FLAG_ADD);
    }

    BOOL result = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                      WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
    if (!result || !WinHttpReceiveResponse(hRequest, NULL))
    {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        SetError("HTTP request failed");
        return false;
    }

    // Read response
    DWORD bytesRead = 0;
    DWORD totalRead = 0;
    char buffer[4096];
    response[0] = '\0';

    while (WinHttpReadData(hRequest, buffer, sizeof(buffer) - 1, &bytesRead) && bytesRead > 0)
    {
        buffer[bytesRead] = '\0';
        int remaining = responseSize - totalRead - 1;
        if (remaining > 0)
        {
            strncat_s(response, responseSize, buffer, min((int)bytesRead, remaining));
            totalRead += min((int)bytesRead, remaining);
        }
        bytesRead = 0;
    }

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return true;
}

bool PlmBridge::HttpPost(const char* path, const char* jsonBody, char* response, int responseSize)
{
    // Similar to HttpGet but with POST method and JSON body
    // TODO: Implement using WinHTTP POST
    SetError("HttpPost not yet implemented");
    return false;
}

bool PlmBridge::HttpPostMultipart(const char* path, const char* filePath,
                                   const char* comment, char* response, int responseSize)
{
    // Multipart/form-data file upload using WinHTTP
    // TODO: Implement boundary construction and binary file reading
    SetError("HttpPostMultipart not yet implemented");
    return false;
}

bool PlmBridge::HttpDelete(const char* path, char* response, int responseSize)
{
    // Similar to HttpGet but with DELETE method
    SetError("HttpDelete not yet implemented");
    return false;
}

void PlmBridge::SaveConfig()
{
    HKEY hKey;
    if (RegCreateKeyExA(HKEY_CURRENT_USER, REGISTRY_PATH, 0, NULL,
                         REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKey, NULL) == ERROR_SUCCESS)
    {
        RegSetValueExA(hKey, "ServerUrl", 0, REG_SZ, (BYTE*)_serverUrl, (DWORD)strlen(_serverUrl) + 1);
        if (_token[0])
            RegSetValueExA(hKey, "AuthToken", 0, REG_SZ, (BYTE*)_token, (DWORD)strlen(_token) + 1);
        RegCloseKey(hKey);
    }
}

void PlmBridge::LoadConfig()
{
    HKEY hKey;
    if (RegOpenKeyExA(HKEY_CURRENT_USER, REGISTRY_PATH, 0, KEY_READ, &hKey) == ERROR_SUCCESS)
    {
        DWORD size = sizeof(_serverUrl);
        RegQueryValueExA(hKey, "ServerUrl", NULL, NULL, (BYTE*)_serverUrl, &size);

        size = sizeof(_token);
        if (RegQueryValueExA(hKey, "AuthToken", NULL, NULL, (BYTE*)_token, &size) == ERROR_SUCCESS)
        {
            if (_token[0]) _loggedIn = true;
        }
        RegCloseKey(hKey);
    }
}

// Placeholder implementations for API methods
int PlmBridge::GetParts(const char* search, PartInfo* parts, int maxParts) { return 0; }
bool PlmBridge::GetPart(const char* partId, PartInfo& part) { return false; }
bool PlmBridge::Checkout(const char* partId, PartInfo& updatedPart) { return false; }
bool PlmBridge::Checkin(const char* partId, const char* filePath, PartInfo& updatedPart) { return false; }
bool PlmBridge::Publish(const char* partId, PartInfo& updatedPart) { return false; }
bool PlmBridge::CreatePart(const char* name, const char* type, const char* subsystem,
                            const char* templateId, PartInfo& newPart) { return false; }
int PlmBridge::GetVersions(const char* partId, VersionInfo* versions, int maxVersions) { return 0; }
bool PlmBridge::DownloadVersion(const char* partId, const char* versionId, const char* savePath) { return false; }
int PlmBridge::GetTemplates(TemplateInfo* templates, int maxTemplates) { return 0; }
bool PlmBridge::GetNextPartNumber(const char* templateId, const char* subsystemCode,
                                   const char* partType, char* partNumber, int bufSize) { return false; }
bool PlmBridge::CreateBranch(const char* partId, const char* branchName, PartInfo& newBranch) { return false; }
