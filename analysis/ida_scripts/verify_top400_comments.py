"""
Verify that Top 400 functions have comments in IDA database.
"""

import idc
import idaapi
import json

def main():
    print("="*70)
    print("VERIFYING TOP 400 COMMENTS")
    print("="*70)
    
    idaapi.auto_wait()
    
    # Top 400 batch 1 + batch 2 addresses
    top400_addrs = [
        # Batch 1
        0x02C53B, 0x02C8AB, 0x02C8C9, 0x02C8D3, 0x02C905, 0x02C919, 0x036FE5,
        0x100BD0, 0x101659, 0x12FA2A,
        0x1573C3, 0x181BC7, 0x1A0A0F, 0x11CF6A, 0x122595,
        # Batch 2
        0x128028, 0x128042, 0x130CE7, 0x133BD5, 0x13ABA7,
        0x1558C8, 0x16F4B1, 0x172436, 0x17B2B6,
        0x196BB9, 0x19FE2D, 0x02C185, 0x0345FD
    ]
    
    results = []
    has_comment = 0
    no_comment = 0
    
    for addr in top400_addrs:
        func_name = idc.get_func_name(addr)
        comment = idc.get_func_cmt(addr, 0)  # 0 = regular comment
        
        has_cmt = bool(comment and comment.strip())
        if has_cmt:
            has_comment += 1
            status = "✓"
        else:
            no_comment += 1
            status = "✗"
        
        results.append({
            'address': hex(addr),
            'name': func_name,
            'has_comment': has_cmt,
            'comment': comment if has_cmt else None
        })
        
        print(f"{status} {addr:#08x} {func_name:40} - {'HAS COMMENT' if has_cmt else 'NO COMMENT'}")
        if has_cmt and comment:
            print(f"     {comment[:100]}...")
    
    print(f"\n{'='*70}")
    print(f"Functions with comments: {has_comment}/{len(top400_addrs)} ({has_comment*100//len(top400_addrs)}%)")
    print(f"Functions without comments: {no_comment}/{len(top400_addrs)}")
    print(f"{'='*70}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top400_comment_verification.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total': len(top400_addrs),
            'with_comments': has_comment,
            'without_comments': no_comment,
            'functions': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
