#ifndef PlmBridge_H
#define PlmBridge_H

/**
 * PLM API Bridge - HTTP communication with FSAE-PLM backend.
 *
 * Uses Windows WinHTTP API for HTTP requests and nlohmann/json for JSON parsing.
 * All methods are synchronous (CAA V5 commands run on CATIA's main thread).
 */
class PlmBridge
{
public:
    PlmBridge();
    ~PlmBridge();

    // Configuration
    void SetServerUrl(const char* url);
    const char* GetServerUrl() const;

    // Authentication
    bool Login(const char* username, const char* password);
    void Logout();
    bool IsLoggedIn() const;
    const char* GetLastError() const;

    // Parts API
    struct PartInfo {
        char id[64];
        char partNumber[128];
        char name[256];
        char type[32];
        char subsystem[64];
        char currentVersion[32];
        char lifecycleState[32];
        char checkState[32];
        char branchName[128];
    };

    struct VersionInfo {
        char id[64];
        char versionNumber[32];
        char fileType[32];
        int fileSize;
        char comment[256];
        char createdAt[64];
    };

    struct TemplateInfo {
        char id[64];
        char name[128];
        char prefix[32];
        char separator[8];
    };

    // API calls
    int GetParts(const char* search, PartInfo* parts, int maxParts);
    bool GetPart(const char* partId, PartInfo& part);
    bool Checkout(const char* partId, PartInfo& updatedPart);
    bool Checkin(const char* partId, const char* filePath, PartInfo& updatedPart);
    bool Publish(const char* partId, PartInfo& updatedPart);
    bool CreatePart(const char* name, const char* type, const char* subsystem,
                    const char* templateId, PartInfo& newPart);
    int GetVersions(const char* partId, VersionInfo* versions, int maxVersions);
    bool DownloadVersion(const char* partId, const char* versionId, const char* savePath);
    int GetTemplates(TemplateInfo* templates, int maxTemplates);
    bool GetNextPartNumber(const char* templateId, const char* subsystemCode,
                           const char* partType, char* partNumber, int bufSize);
    bool CreateBranch(const char* partId, const char* branchName, PartInfo& newBranch);

    // Config persistence (registry)
    void SaveConfig();
    void LoadConfig();

private:
    char _serverUrl[256];
    char _token[2048];
    char _lastError[512];
    bool _loggedIn;

    bool HttpGet(const char* path, char* response, int responseSize);
    bool HttpPost(const char* path, const char* jsonBody, char* response, int responseSize);
    bool HttpPostMultipart(const char* path, const char* filePath,
                           const char* comment, char* response, int responseSize);
    bool HttpDelete(const char* path, char* response, int responseSize);
    void SetError(const char* error);
};

#endif
