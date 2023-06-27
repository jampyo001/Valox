#pragma once
 
#include <Windows.h>
#include <cstdint>
#include <cstddef>
 
class Driver {
public:
    static constexpr uint32_t kReadVmRequest = 0x80000001;
    static constexpr uint32_t kGetPoolRequest = 0x80000002;
    static constexpr uint32_t kMouseRequest = 0x80000003;
 
    Driver() = default;
    ~Driver() = default;
 
    void Initialize(int process_id) {
        HMODULE win32u_dll = LoadLibraryA("win32u.dll");
        if (win32u_dll != nullptr) {
            NtUserGetPointerProprietaryId_ = reinterpret_cast<NtUserGetPointerProprietaryId>(
                GetProcAddress(win32u_dll, "NtUserGetPointerProprietaryId"));
        }
        process_id_ = process_id;
    }
 
    uintptr_t GetGuardedRegion() {
        Request request = {};
        request.request_key = kGetPoolRequest;
        CallDriver(&request);
        guarded_region_ = request.allocation;
        return guarded_region_;
    }
 
    template <typename T>
    T ReadGuarded(uintptr_t src, size_t size = sizeof(T)) {
        T buffer;
        ReadVm(process_id_, src, reinterpret_cast<uintptr_t>(&buffer), size);
        uintptr_t val = guarded_region_ + (*(uintptr_t*)&buffer & 0xFFFFFF);
        return *(T*)&val;
    }
 
    template <typename T>
    T Read(uintptr_t src, size_t size = sizeof(T)) {
        T buffer;
        ReadVm(process_id_, src, reinterpret_cast<uintptr_t>(&buffer), size);
        return buffer;
    }
 
    template<typename T>
    void ReadArray(uintptr_t address, T* array, size_t len) {
        ReadVm(process_id_, address, reinterpret_cast<uintptr_t>(array), sizeof(T) * len);
    }
 
    void MoveMouse(long x, long y) {
        Request request = {};
        request.x = x;
        request.y = y;
        request.request_key = kMouseRequest;
        CallDriver(&request);
    }
 
    void SendInput(unsigned short button) {
        Request request = {};
        request.button_flags = button;
        request.request_key = kMouseRequest;
        CallDriver(&request);
    }
 
private:
    typedef INT64(*NtUserGetPointerProprietaryId)(uintptr_t);
    NtUserGetPointerProprietaryId NtUserGetPointerProprietaryId_ = nullptr;
 
    struct Request {
        uint32_t src_pid;
        uintptr_t src_addr;
        uintptr_t dst_addr;
        size_t size;
        int request_key;
        uintptr_t allocation;  // For kGetPoolRequest
        long x;                // For kMouseRequest
        long y;                // For kMouseRequest
        unsigned short button_flags;  // For kMouseRequest
    };
 
    void ReadVm(uint32_t src_pid, uintptr_t src_addr, uintptr_t dst_addr, size_t size) {
        if (src_pid == 0 || src_addr == 0) {
            return;
        }
        Request request = {src_pid, src_addr, dst_addr, size, kReadVmRequest};
        CallDriver(&request);
    }
 
    void CallDriver(Request* request) {
        if (NtUserGetPointerProprietaryId_ == nullptr) {
            return;
        }
        NtUserGetPointerProprietaryId_(reinterpret_cast<uintptr_t>(request));
    }
 
    int process_id_;
    uintptr_t guarded_region_;
};
 
Driver driver;