// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract VerifiCertRegistry is AccessControl {
    bytes32 public constant ISSUER_ADMIN_ROLE = keccak256("ISSUER_ADMIN_ROLE");
    bytes32 public constant APPROVED_ISSUER_ROLE = keccak256("APPROVED_ISSUER_ROLE");

    struct Certificate {
        bytes32 documentHash;
        address issuer;
        uint256 issuedAt;
        uint256 expiresAt;
        bool revoked;
        string metadataURI;
    }

    mapping(string => Certificate) private certificates;
    mapping(string => bool) private certificateExists;
    mapping(address => bool) private suspendedIssuers;

    event CertificateIssued(string indexed certificateId, bytes32 indexed documentHash, address indexed issuer, uint256 issuedAt, uint256 expiresAt, string metadataURI);
    event CertificateRevoked(string indexed certificateId, address indexed revokedBy);
    event IssuerRegistered(address indexed issuer);
    event IssuerSuspended(address indexed issuer);

    error DuplicateCertificateId();
    error CertificateNotFound();
    error IssuerIsSuspended();
    error NotCertificateIssuerOrAdmin();

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ISSUER_ADMIN_ROLE, admin);
    }

    modifier onlyApprovedIssuer() {
        if (suspendedIssuers[msg.sender]) revert IssuerIsSuspended();
        _checkRole(APPROVED_ISSUER_ROLE, msg.sender);
        _;
    }

    function issueCertificate(
        string calldata certificateId,
        bytes32 documentHash,
        uint256 expiresAt,
        string calldata metadataURI
    ) external onlyApprovedIssuer {
        if (certificateExists[certificateId]) revert DuplicateCertificateId();
        certificates[certificateId] = Certificate({
            documentHash: documentHash,
            issuer: msg.sender,
            issuedAt: block.timestamp,
            expiresAt: expiresAt,
            revoked: false,
            metadataURI: metadataURI
        });
        certificateExists[certificateId] = true;
        emit CertificateIssued(certificateId, documentHash, msg.sender, block.timestamp, expiresAt, metadataURI);
    }

    function verifyCertificate(string calldata certificateId) external view returns (bool exists, bytes32 documentHash, address issuer, bool revoked, uint256 expiresAt) {
        Certificate memory cert = certificates[certificateId];
        return (certificateExists[certificateId], cert.documentHash, cert.issuer, cert.revoked, cert.expiresAt);
    }

    function revokeCertificate(string calldata certificateId) external {
        if (!certificateExists[certificateId]) revert CertificateNotFound();
        Certificate storage cert = certificates[certificateId];
        if (msg.sender != cert.issuer && !hasRole(DEFAULT_ADMIN_ROLE, msg.sender)) revert NotCertificateIssuerOrAdmin();
        cert.revoked = true;
        emit CertificateRevoked(certificateId, msg.sender);
    }

    function getCertificate(string calldata certificateId) external view returns (Certificate memory) {
        if (!certificateExists[certificateId]) revert CertificateNotFound();
        return certificates[certificateId];
    }

    function registerIssuer(address issuer) external onlyRole(ISSUER_ADMIN_ROLE) {
        suspendedIssuers[issuer] = false;
        _grantRole(APPROVED_ISSUER_ROLE, issuer);
        emit IssuerRegistered(issuer);
    }

    function suspendIssuer(address issuer) external onlyRole(ISSUER_ADMIN_ROLE) {
        suspendedIssuers[issuer] = true;
        _revokeRole(APPROVED_ISSUER_ROLE, issuer);
        emit IssuerSuspended(issuer);
    }

    function isApprovedIssuer(address issuer) external view returns (bool) {
        return hasRole(APPROVED_ISSUER_ROLE, issuer) && !suspendedIssuers[issuer];
    }
}
