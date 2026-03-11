// SPDX-License-Identifier: GPL-3.0
//
// This example demonstrates calling of IStaking precompile
// from another smart contract

pragma solidity ^0.8.3;

address constant ISTAKING_ADDRESS = 0x0000000000000000000000000000000000000805;

interface IStaking {
    function addStake(bytes32 hotkey, uint256 amount, uint256 netuid) external payable;
    
    function removeStake(bytes32 hotkey, uint256 amount, uint256 netuid) external payable;
    
    function moveStake(
        bytes32 origin_hotkey,
        bytes32 destination_hotkey,
        uint256 origin_netuid,
        uint256 destination_netuid,
        uint256 amount
    ) external payable;
    
    function transferStake(
        bytes32 destination_coldkey,
        bytes32 hotkey,
        uint256 origin_netuid,
        uint256 destination_netuid,
        uint256 amount
    ) external payable;
    
    function addStakeLimit(
        bytes32 hotkey,
        uint256 amount,
        uint256 limit_price,
        bool allow_partial,
        uint256 netuid
    ) external payable;
    
    function removeStakeLimit(
        bytes32 hotkey,
        uint256 amount,
        uint256 limit_price,
        bool allow_partial,
        uint256 netuid
    ) external payable;
}

contract StakeWrap {
    address public owner;
    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    receive() external payable {}

    /**
     * @notice Stake TAO to a hotkey (creates alpha tokens)
     * @param hotkey The hotkey public key (32 bytes)
     * @param netuid The subnet ID
     * @param amount The amount to stake in rao (TAO)
     */
    function stake(
        bytes32 hotkey,
        uint256 netuid,
        uint256 amount
    ) external onlyOwner {
        bytes memory data = abi.encodeWithSelector(
            IStaking.addStake.selector,
            hotkey,
            amount,
            netuid
        );
        (bool success, bytes memory returnData) = ISTAKING_ADDRESS.call{gas: gasleft()}(data);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("addStake call failed");
        }
    }

    /**
     * @notice Stake TAO to a hotkey with a price limit (creates alpha tokens)
     * @param hotkey The hotkey public key (32 bytes)
     * @param netuid The subnet ID
     * @param limitPrice The price limit in rao per alpha
     * @param amount The amount to stake in rao (TAO)
     * @param allowPartial Whether to allow partial stake
     */
    function stakeLimit(
        bytes32 hotkey,
        uint256 netuid,
        uint256 limitPrice,
        uint256 amount,
        bool allowPartial
    ) external onlyOwner {
        bytes memory data = abi.encodeWithSelector(
            IStaking.addStakeLimit.selector,
            hotkey,
            amount,
            limitPrice,
            allowPartial,
            netuid
        );
        (bool success, bytes memory returnData) = ISTAKING_ADDRESS.call{gas: gasleft()}(data);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("addStakeLimit call failed");
        }
    }

    /**
     * @notice Unstake alpha tokens (returns TAO)
     * @param hotkey The hotkey public key (32 bytes)
     * @param netuid The subnet ID
     * @param amount The amount to unstake in alpha (NOT rao!)
     */
    function removeStake(
        bytes32 hotkey,
        uint256 netuid,
        uint256 amount
    ) external onlyOwner {
        bytes memory data = abi.encodeWithSelector(
            IStaking.removeStake.selector,
            hotkey,
            amount,
            netuid
        );
        (bool success, bytes memory returnData) = ISTAKING_ADDRESS.call{gas: gasleft()}(data);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("removeStake call failed");
        }
    }
    
    /**
     * @notice Transfer stake (alpha) to another coldkey
     * @dev This allows the contract to receive alpha tokens from other accounts
     * @param destination_coldkey The destination coldkey (32 bytes)
     * @param hotkey The hotkey public key (32 bytes)
     * @param origin_netuid The origin subnet ID
     * @param destination_netuid The destination subnet ID
     * @param amount The amount to transfer in rao
     */
    function transferStake(
        bytes32 destination_coldkey,
        bytes32 hotkey,
        uint256 origin_netuid,
        uint256 destination_netuid,
        uint256 amount
    ) external onlyOwner {
        bytes memory data = abi.encodeWithSelector(
            IStaking.transferStake.selector,
            destination_coldkey,
            hotkey,
            origin_netuid,
            destination_netuid,
            amount
        );
        (bool success, bytes memory returnData) = ISTAKING_ADDRESS.call{gas: gasleft()}(data);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("transferStake call failed");
        }
    }
    
    /**
     * @notice Move stake from one hotkey to another
     * @param origin_hotkey The origin hotkey (32 bytes)
     * @param destination_hotkey The destination hotkey (32 bytes)
     * @param origin_netuid The origin subnet ID
     * @param destination_netuid The destination subnet ID
     * @param amount The amount to move in rao
     */
    function moveStake(
        bytes32 origin_hotkey,
        bytes32 destination_hotkey,
        uint256 origin_netuid,
        uint256 destination_netuid,
        uint256 amount
    ) external onlyOwner {
        bytes memory data = abi.encodeWithSelector(
            IStaking.moveStake.selector,
            origin_hotkey,
            destination_hotkey,
            origin_netuid,
            destination_netuid,
            amount
        );
        (bool success, bytes memory returnData) = ISTAKING_ADDRESS.call{gas: gasleft()}(data);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("moveStake call failed");
        }
    }

    /**
     * @notice Withdraw all TAO from the contract to the owner
     */
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        (bool success, ) = payable(owner).call{value: balance}("");
        require(success, "Withdrawal failed");
    }

    /**
     * @notice Withdraw a specific amount of TAO from the contract to the owner
     * @param amount The amount of TAO to withdraw (in rao)
     */
    function withdraw(uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than 0");
        require(address(this).balance >= amount, "Insufficient balance");
        (bool success, ) = payable(owner).call{value: amount}("");
        require(success, "Withdrawal failed");
    }

    /**
     * @notice Withdraw TAO to a specific address
     * @param to The address to withdraw to
     * @param amount The amount of TAO to withdraw (in rao)
     */
    function withdrawTo(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid recipient address");
        require(amount > 0, "Amount must be greater than 0");
        require(address(this).balance >= amount, "Insufficient balance");
        (bool success, ) = payable(to).call{value: amount}("");
        require(success, "Withdrawal failed");
    }
}

